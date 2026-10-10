import AppKit
import SceneKit
import simd

/// Minimal glTF 2 reader for the uncompressed, rigged sample character.
/// Unsupported/compressed data is rejected instead of rendering a broken asset.
final class GLBCharacter {
    let root = SCNNode()
    private(set) var nodes: [SCNNode] = []
    private var json: [String: Any] = [:]
    private var binary = Data()
    private var images: [Int:NSImage] = [:]
    private var rest: [String: simd_quatf] = [:]
    private var phase: Float = 0
    private var blend: Float = 0
    private struct SkinMesh {
        let node:SCNNode
        let positions:[Float],normals:[Float],weights:[Float],joints:[Int]
        let bones:[SCNNode],inverse:[simd_float4x4]
        let uv:SCNGeometrySource?,element:SCNGeometryElement,material:SCNMaterial
    }
    private var skinMeshes:[SkinMesh]=[]
    private var skinAccumulator:Float=1

    init(url: URL, textures: URL) throws {
        let bytes = try Data(contentsOf:url)
        func uint(_ i:Int)->UInt32 { bytes.withUnsafeBytes { $0.loadUnaligned(fromByteOffset:i,as:UInt32.self) } }
        guard uint(0)==0x46546C67, uint(4)==2 else { throw NSError(domain:"GLB",code:1) }
        let length=Int(uint(12))
        json = try JSONSerialization.jsonObject(with:bytes.subdata(in:20..<20+length)) as! [String:Any]
        binary = bytes.subdata(in:(28+length)..<bytes.count)
        let nodeDefs=json["nodes"] as! [[String:Any]]
        nodes=nodeDefs.map { def in
            let n=SCNNode(); n.name=def["name"] as? String
            if let t=(def["translation"] as? [NSNumber])?.map({$0.floatValue}) { n.simdPosition=SIMD3(t[0],t[1],t[2]) }
            if let s=(def["scale"] as? [NSNumber])?.map({$0.floatValue}) { n.simdScale=SIMD3(s[0],s[1],s[2]) }
            if let r=(def["rotation"] as? [NSNumber])?.map({$0.floatValue}) { n.simdOrientation=simd_quatf(ix:r[0],iy:r[1],iz:r[2],r:r[3]) }
            if let m=(def["matrix"] as? [NSNumber])?.map({$0.floatValue}) { n.simdTransform=matrix(m) }
            return n
        }
        for (i,def) in nodeDefs.enumerated() {
            for c in def["children"] as? [Int] ?? [] { nodes[i].addChildNode(nodes[c]) }
        }
        let scenes=json["scenes"] as! [[String:Any]]
        for index in scenes[(json["scene"] as? Int) ?? 0]["nodes"] as! [Int] { root.addChildNode(nodes[index]) }
        let meshes=json["meshes"] as! [[String:Any]]
        let skins=json["skins"] as? [[String:Any]] ?? []
        for (i,def) in nodeDefs.enumerated() {
            guard let meshIndex=def["mesh"] as? Int else { continue }
            for primitive in meshes[meshIndex]["primitives"] as! [[String:Any]] {
                let attrs=primitive["attributes"] as! [String:Int]
                var sources=[source(attrs["POSITION"]!,semantic:.vertex)]
                if let n=attrs["NORMAL"] { sources.append(source(n,semantic:.normal)) }
                if let uv=attrs["TEXCOORD_0"] { sources.append(source(uv,semantic:.texcoord)) }
                let index=accessor(primitive["indices"] as! Int)
                let elem=SCNGeometryElement(data:index.data,primitiveType:.triangles,
                    primitiveCount:index.count/3,bytesPerIndex:index.bytes)
                let geo=SCNGeometry(sources:sources,elements:[elem])
                let mat=SCNMaterial(); mat.lightingModel = .physicallyBased
                let defs=json["materials"] as! [[String:Any]]
                let md=defs[primitive["material"] as? Int ?? 0]
                mat.name=md["name"] as? String
                let pbr=md["pbrMetallicRoughness"] as? [String:Any] ?? [:]
                let base=(pbr["baseColorFactor"] as? [NSNumber])?.map({$0.doubleValue}) ?? [1,1,1,1]
                mat.diffuse.contents=NSColor(calibratedRed:base[0],green:base[1],blue:base[2],alpha:base[3])
                if let t=pbr["baseColorTexture"] as? [String:Any] {
                    mat.diffuse.contents=image(t["index"] as! Int,folder:textures)
                }
                if let t=md["normalTexture"] as? [String:Any] {
                    mat.normal.contents=image(t["index"] as! Int,folder:textures)
                }
                mat.metalness.contents=pbr["metallicFactor"] as? Double ?? 1.0
                mat.roughness.contents=pbr["roughnessFactor"] as? Double ?? 1.0
                if let t=pbr["metallicRoughnessTexture"] as? [String:Any],let map=image(t["index"] as! Int,folder:textures) {
                    mat.roughness.contents=map;mat.roughness.textureComponents = .green
                    mat.metalness.contents=map;mat.metalness.textureComponents = .blue
                }
                if let e=(md["emissiveFactor"] as? [NSNumber])?.map({$0.doubleValue}) {
                    mat.emission.contents=NSColor(calibratedRed:e[0],green:e[1],blue:e[2],alpha:1)
                    if let t=md["emissiveTexture"] as? [String:Any] {mat.emission.contents=image(t["index"] as! Int,folder:textures)}
                    let ext=md["extensions"] as? [String:Any]
                    mat.emission.intensity=((ext?["KHR_materials_emissive_strength"] as? [String:Any])?["emissiveStrength"] as? Double) ?? 1
                }
                if (md["alphaMode"] as? String)=="BLEND" {
                    mat.transparencyMode = .aOne;mat.blendMode = .alpha
                    mat.writesToDepthBuffer=false
                    mat.transparency=CGFloat(base[3])
                }
                mat.isDoubleSided=md["doubleSided"] as? Bool ?? false
                for prop in [mat.diffuse,mat.normal,mat.roughness,mat.metalness,mat.emission] {prop.wrapS = .repeat;prop.wrapT = .repeat}
                geo.materials=[mat]
                let render=SCNNode(geometry:geo); render.castsShadow=true
                nodes[i].addChildNode(render)
                if let skinIndex=def["skin"] as? Int,
                   let joints=attrs["JOINTS_0"],let weights=attrs["WEIGHTS_0"] {
                    let skin=skins[skinIndex]
                    let bones=(skin["joints"] as! [Int]).map { nodes[$0] }
                    let inv=accessor(skin["inverseBindMatrices"] as! Int)
                    let numbers=floats(inv.data)
                    let transforms=(0..<inv.count).map { j in matrix(Array(numbers[j*16..<j*16+16])) }
                    render.removeFromParentNode();root.addChildNode(render)
                    // This preview evaluates this small sample rig explicitly.
                    // glTF and SceneKit disagree on the FBX root's bind-space
                    // convention; using the glTF equation preserves the pose.
                    let jointData=accessor(joints)
                    let jointValues=(0..<jointData.count*jointData.components).map { j -> Int in
                        jointData.data.withUnsafeBytes { p in
                            jointData.bytes==1 ? Int(p[j]) : Int(p.loadUnaligned(fromByteOffset:j*jointData.bytes,as:UInt16.self))
                        }
                    }
                    skinMeshes.append(SkinMesh(node:render,
                        positions:floats(accessor(attrs["POSITION"]!).data),
                        normals:floats(accessor(attrs["NORMAL"]!).data),
                        weights:floats(accessor(weights).data),joints:jointValues,
                        bones:bones,inverse:transforms,
                        uv:attrs["TEXCOORD_0"].map {source($0,semantic:.texcoord)},
                        element:elem,material:mat))
                }
            }
        }
        // Adopt TPose's sample transforms, then lower the arms to a neutral stance.
        if let animations=json["animations"] as? [[String:Any]],
           let pose=animations.first(where: { ($0["name"] as? String)=="TPose" }) {
            let samplers=pose["samplers"] as! [[String:Any]]
            for ch in pose["channels"] as! [[String:Any]] {
                let target=ch["target"] as! [String:Any]
                let n=nodes[target["node"] as! Int]
                let s=samplers[ch["sampler"] as! Int]
                let f=floats(accessor(s["output"] as! Int).data)
                switch target["path"] as? String {
                case "rotation": n.simdOrientation=simd_quatf(ix:f[0],iy:f[1],iz:f[2],r:f[3])
                case "translation": n.simdPosition=SIMD3(f[0],f[1],f[2])
                case "scale": n.simdScale=SIMD3(f[0],f[1],f[2])
                default: break
                }
            }
        }
        // Bone local axes differ from world axes. Aim each upper arm down in world
        // space, then convert the rotation back into its parent space.
        for suffix in ["LeftArm","RightArm"] {
            if let arm=nodes.first(where:{$0.name?.hasSuffix(suffix)==true}),
               let fore=arm.childNodes.first,let parent=arm.parent {
                let direction=simd_normalize(fore.simdWorldPosition-arm.simdWorldPosition)
                let target=simd_normalize(SIMD3<Float>(suffix=="LeftArm" ? 0.14 : -0.14,-1,0.04))
                let aim=simd_quatf(from:direction,to:target)
                arm.simdOrientation=parent.simdWorldOrientation.inverse*aim*arm.simdWorldOrientation
            }
        }
        for n in nodes { if let name=n.name { rest[name]=n.simdOrientation } }
        animate(delta:0,speed:0)
    }

    private func matrix(_ f:[Float])->simd_float4x4 {
        simd_float4x4(columns:(SIMD4(f[0],f[1],f[2],f[3]),SIMD4(f[4],f[5],f[6],f[7]),
            SIMD4(f[8],f[9],f[10],f[11]),SIMD4(f[12],f[13],f[14],f[15])))
    }
    private func floats(_ data:Data)->[Float] {
        (0..<data.count/4).map { i in data.withUnsafeBytes { $0.loadUnaligned(fromByteOffset:i*4,as:Float.self) } }
    }
    private func image(_ index:Int,folder:URL)->NSImage? {
        let defs=json["textures"] as! [[String:Any]]
        let i=defs[index]["source"] as! Int
        if let cached=images[i] {return cached}
        let imageDefs=json["images"] as? [[String:Any]] ?? []
        if i<imageDefs.count,let v=imageDefs[i]["bufferView"] as? Int {
            let buffer=(json["bufferViews"] as! [[String:Any]])[v]
            let offset=buffer["byteOffset"] as? Int ?? 0, length=buffer["byteLength"] as! Int
            if let loaded=NSImage(data:binary.subdata(in:offset..<offset+length)) {images[i]=loaded;return loaded}
        }
        return NSImage(contentsOf:folder.appendingPathComponent("character-\(i).png"))
            ?? NSImage(contentsOf:folder.appendingPathComponent("character-\(i).jpg"))
    }
    private struct Accessor { let data:Data; let count:Int; let components:Int; let bytes:Int; let float:Bool }
    private func accessor(_ index:Int)->Accessor {
        let a=(json["accessors"] as! [[String:Any]])[index]
        let v=(json["bufferViews"] as! [[String:Any]])[a["bufferView"] as! Int]
        let type=a["componentType"] as! Int
        let bytes=type==5126 || type==5125 ? 4 : (type==5123 || type==5122 ? 2 : 1)
        let comps=["SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16][a["type"] as! String]!
        let count=a["count"] as! Int
        let start=(v["byteOffset"] as? Int ?? 0)+(a["byteOffset"] as? Int ?? 0)
        let stride=v["byteStride"] as? Int ?? bytes*comps
        var data=Data();data.reserveCapacity(count*comps*bytes)
        for i in 0..<count { data.append(binary.subdata(in:start+i*stride..<start+i*stride+comps*bytes)) }
        return Accessor(data:data,count:count,components:comps,bytes:bytes,float:type==5126)
    }
    private func source(_ index:Int,semantic:SCNGeometrySource.Semantic)->SCNGeometrySource {
        let a=accessor(index)
        if semantic == .boneIndices && a.bytes==1 {
            var expanded=Data();expanded.reserveCapacity(a.data.count*2)
            for byte in a.data {var value=UInt16(byte);withUnsafeBytes(of:&value) {expanded.append(contentsOf:$0)}}
            return SCNGeometrySource(data:expanded,semantic:semantic,vectorCount:a.count,usesFloatComponents:false,
                componentsPerVector:a.components,bytesPerComponent:2,dataOffset:0,dataStride:2*a.components)
        }
        return SCNGeometrySource(data:a.data,semantic:semantic,vectorCount:a.count,usesFloatComponents:a.float,
            componentsPerVector:a.components,bytesPerComponent:a.bytes,dataOffset:0,dataStride:a.bytes*a.components)
    }
    func animate(delta:Float,speed:Float) {
        phase += delta * (speed>0.1 ? 7.2 : 1.2)
        blend += (min(speed/1.5,1)-blend)*min(delta*8,1)
        for n in nodes {
            guard let name=n.name,let base=rest[name] else { continue }
            var angle:Float=0;let axis=SIMD3<Float>(1,0,0)
            if name.hasSuffix("LeftArm") { angle = -sin(phase)*0.18*blend }
            if name.hasSuffix("RightArm") { angle = sin(phase)*0.18*blend }
            if name.hasSuffix("LeftUpLeg") { angle = sin(phase)*0.34*blend }
            if name.hasSuffix("RightUpLeg") { angle = -sin(phase)*0.34*blend }
            if name.hasSuffix("LeftLeg") { angle = max(0,-sin(phase))*0.40*blend }
            if name.hasSuffix("RightLeg") { angle = max(0,sin(phase))*0.40*blend }
            if name.hasSuffix("LeftForeArm") || name.hasSuffix("RightForeArm") { angle = -0.10 }
            if name.hasSuffix("Spine1") { angle = sin(phase)*0.007 }
            n.simdOrientation=base*simd_quatf(angle:angle,axis:axis)
        }
        skinAccumulator += delta
        guard skinAccumulator>=1.0/30 || delta==0 else {return}
        skinAccumulator=0
        let rootInverse=root.simdWorldTransform.inverse
        for mesh in skinMeshes {
            let transforms=zip(mesh.bones,mesh.inverse).map {rootInverse*$0.0.simdWorldTransform*$0.1}
            var positions=[SIMD3<Float>](),normals=[SIMD3<Float>]()
            let count=mesh.positions.count/3
            positions.reserveCapacity(count);normals.reserveCapacity(count)
            for v in 0..<count {
                let p=SIMD4<Float>(mesh.positions[v*3],mesh.positions[v*3+1],mesh.positions[v*3+2],1)
                let n=SIMD4<Float>(mesh.normals[v*3],mesh.normals[v*3+1],mesh.normals[v*3+2],0)
                var finalP=SIMD4<Float>(repeating:0),finalN=SIMD4<Float>(repeating:0)
                for k in 0..<4 {
                    let w=mesh.weights[v*4+k];if w<0.00001 {continue}
                    let m=transforms[mesh.joints[v*4+k]]
                    finalP += (m*p)*w;finalN += (m*n)*w
                }
                positions.append(SIMD3(finalP.x,finalP.y,finalP.z))
                normals.append(simd_normalize(SIMD3(finalN.x,finalN.y,finalN.z)))
            }
            func source(_ values:[SIMD3<Float>],_ semantic:SCNGeometrySource.Semantic)->SCNGeometrySource {
                let data=values.withUnsafeBytes {Data($0)}
                return SCNGeometrySource(data:data,semantic:semantic,vectorCount:values.count,usesFloatComponents:true,
                    componentsPerVector:3,bytesPerComponent:4,dataOffset:0,dataStride:MemoryLayout<SIMD3<Float>>.stride)
            }
            var sources=[source(positions,.vertex),source(normals,.normal)]
            if let uv=mesh.uv {sources.append(uv)}
            let geometry=SCNGeometry(sources:sources,elements:[mesh.element]);geometry.materials=[mesh.material]
            mesh.node.geometry=geometry
        }
    }
    func setFirstPerson(_ enabled:Bool) {
        root.isHidden=false
        for mesh in skinMeshes {
            mesh.node.isHidden=enabled && !(mesh.material.name?.contains("body") ?? false)
        }
    }
}
