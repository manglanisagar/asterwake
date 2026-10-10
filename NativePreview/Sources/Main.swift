import AppKit
import SceneKit
import QuartzCore
import simd

struct Layout: Decodable {
    struct Material:Decodable { var color:[Double];var roughness:Double;var metalness:Double;var emission:[Double]? }
    struct Item:Decodable {var name:String;var shape:String;var position:[Float];var size:[Double];var material:String;var collision:Bool;var group:String;var rotation:[Float]?}
    struct Earth:Decodable {var position:[Float];var radius:Double}
    var materials:[String:Material];var objects:[Item];var spawn:[Float];var earth:Earth;var roomBounds:[[Float]]
}

func vec(_ a:[Float])->SIMD3<Float> { SIMD3(a[0],a[1],a[2]) }
func color(_ a:[Double])->NSColor { NSColor(srgbRed:a[0],green:a[1],blue:a[2],alpha:1) }

final class GameView:SCNView {
    weak var game:Habitat?
    override var acceptsFirstResponder:Bool { true }
    override func keyDown(with event:NSEvent) { game?.key(event.keyCode,down:true,repeatKey:event.isARepeat) }
    override func keyUp(with event:NSEvent) { game?.key(event.keyCode,down:false,repeatKey:false) }
    override func flagsChanged(with event:NSEvent) { game?.sprint=event.modifierFlags.contains(.shift) }
    override func mouseDown(with event:NSEvent) { game?.captureMouse() }
    override func mouseMoved(with event:NSEvent) {
        if game?.mouseCaptured == true { game?.look(dx:Float(event.deltaX),dy:Float(event.deltaY)) }
    }
    override func mouseDragged(with event:NSEvent) { game?.look(dx:Float(event.deltaX),dy:Float(event.deltaY)) }
    override func rightMouseDragged(with event:NSEvent) { game?.look(dx:Float(event.deltaX),dy:Float(event.deltaY)) }
    override func scrollWheel(with event:NSEvent) { game?.cameraDistance=max(1.4,min(4.5,(game?.cameraDistance ?? 3.0)+Float(event.deltaY)*0.06)) }
}

final class Habitat:NSObject {
    let scene=SCNScene(),camera=SCNNode(),player=SCNNode(),earth=SCNNode()
    let view:GameView
    let layout:Layout
    let assetURL:URL
    let status=NSTextField(labelWithString:""),prompt=NSTextField(labelWithString:""),mode=NSTextField(labelWithString:"")
    var timer:Timer?,lastTime=0.0,clock=0.0
    var pressed=Set<UInt16>(),sprint=false,mouseCaptured=false
    var yaw:Float=0,pitch:Float = -0.04,cameraDistance:Float=3.0,thirdPerson=true
    var doors:[SCNNode]=[],shutters:[SCNNode]=[],lamps:[SCNNode]=[]
    var doorOpen=false,shutterClosed=false,lightsOn=true,night=false,highQuality=true
    var lightLevel:CGFloat=1,starLevel:CGFloat=0.01
    var ambient=SCNNode(),sun=SCNNode(),character:GLBCharacter?
    var existingCabin:GLBCharacter?
    var usesExistingCabin=false
    var earthMaterial=SCNMaterial(),stars:SCNNode?
    var materials:[String:SCNMaterial]=[:]
    var obstacles:[Layout.Item]=[]
    var bob:Float=0
    let stateURL:URL

    init(view:GameView,assets:URL) throws {
        self.view=view;assetURL=assets
        var decoded=try JSONDecoder().decode(Layout.self,from:Data(contentsOf:assets.appendingPathComponent("layout.json")))
        usesExistingCabin=FileManager.default.fileExists(atPath:assets.appendingPathComponent("Source/EndlessJourneyCabin.glb").path)
        if usesExistingCabin {decoded.spawn=[0,0,1.25];decoded.roomBounds=[[-2.7,2.8,-2.5,2.25]]}
        layout=decoded
        let projectRoot=assets.path.contains(".app/Contents/")
            ? Bundle.main.bundleURL.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            : assets.deletingLastPathComponent()
        stateURL=projectRoot.appendingPathComponent("Saved/native-state.json")
        super.init()
        view.game=self;view.scene=scene;view.backgroundColor = .black
        view.preferredFramesPerSecond=60;view.antialiasingMode = .multisampling4X
        view.autoenablesDefaultLighting=false;view.allowsCameraControl=false
        view.isPlaying=true;view.rendersContinuously=true
        scene.physicsWorld.gravity=SCNVector3(0,-9.8,0)
        buildMaterials();buildShip();buildEarth();buildLighting();buildCharacter();buildCamera();buildOverlay()
        if !CommandLine.arguments.contains("--snapshot"),
            let data=try? Data(contentsOf:stateURL),let state=try? JSONSerialization.jsonObject(with:data) as? [String:Any],
            state["build"] as? Int == (usesExistingCabin ? 3 : 2),
            let pos=state["position"] as? [Float],pos.count==3,validPosition(vec(pos)) {
            player.simdPosition=vec(pos);yaw=state["yaw"] as? Float ?? 0
        }
        updateCamera(delta:1,speed:0)
    }
    func texture(_ name:String)->NSImage? { NSImage(contentsOf:assetURL.appendingPathComponent("Textures/\(name)")) }
    func buildMaterials() {
        for (name,def) in layout.materials {
            let m=SCNMaterial();m.name=name;m.lightingModel = .physicallyBased
            m.diffuse.contents=color(def.color);m.roughness.contents=def.roughness;m.metalness.contents=def.metalness
            if let e=def.emission {m.emission.contents=color(e);m.emission.intensity=0.8}
            if ["panel","floor","fabric"].contains(name),let image=texture("\(name)-detail.jpg") {
                m.diffuse.contents=image
                m.diffuse.wrapS = .repeat;m.diffuse.wrapT = .repeat
                let uv:CGFloat=name=="fabric" ? 3 : 1
                m.diffuse.contentsTransform=SCNMatrix4MakeScale(uv,uv,1)
            }
            materials[name]=m
        }
    }
    func buildShip() {
        if usesExistingCabin {
            do {
                existingCabin=try GLBCharacter(url:assetURL.appendingPathComponent("Source/EndlessJourneyCabin.glb"),textures:assetURL.appendingPathComponent("Textures"))
                let room=existingCabin!.root;room.eulerAngles.y = .pi
                room.enumerateChildNodes { node,_ in
                    if node.geometry?.materials.first?.name=="Glass" {node.opacity=0.01;node.castsShadow=false}
                }
                room.name="Endless Journey — MASSX-RZ";scene.rootNode.addChildNode(room)
                // Close the artwork's off-camera gaps with an outer hull.
                let hull=SCNMaterial();hull.lightingModel = .physicallyBased;hull.diffuse.contents=NSColor(white:0.045,alpha:1);hull.roughness.contents=0.8
                for (p,s) in [
                    (SCNVector3(0,-0.09,0),SCNVector3(6.3,0.08,5.5)),
                    (SCNVector3(-3.1,1.5,0),SCNVector3(0.05,3.2,5.5)),
                    (SCNVector3(3.1,1.5,0),SCNVector3(0.05,3.2,5.5)),
                    (SCNVector3(0,1.5,2.55),SCNVector3(6.3,3.2,0.05)),
                    (SCNVector3(-2.12,1.5,-2.78),SCNVector3(1.85,3.2,0.05)),
                    (SCNVector3(2.12,1.5,-2.78),SCNVector3(1.85,3.2,0.05)),
                    (SCNVector3(0,0.39,-2.78),SCNVector3(2.4,0.96,0.05)),
                    (SCNVector3(0,2.66,-2.78),SCNVector3(2.4,1.04,0.05))
                ] {let b=SCNBox(width:CGFloat(s.x),height:CGFloat(s.y),length:CGFloat(s.z),chamferRadius:0);b.materials=[hull];let n=SCNNode(geometry:b);n.position=p;scene.rootNode.addChildNode(n)}
                for (name,p,size) in [
                    ("bed",[Float(0),0.7,-2.15],[Double(2.9),1.1,0.8]),
                    ("workstation",[Float(2.25),0.75,-1.65],[Double(0.95),1.5,1.1]),
                    ("storage",[Float(2.65),1.1,0.2],[Double(0.55),2.2,2.8]),
                    ("sink",[Float(-2.55),0.8,-1.6],[Double(0.65),1.6,1.3])
                ] {obstacles.append(Layout.Item(name:name,shape:"box",position:p,size:size,material:"metal",collision:true,group:"furniture",rotation:nil))}
            } catch {NSLog("Cabin import failed: %@",String(describing:error))}
            return
        }
        for item in layout.objects {
            let b=SCNBox(width:item.size[0],height:item.size[1],length:item.size[2],chamferRadius:min(0.018,item.size.min()!*0.16))
            b.chamferSegmentCount=2;b.materials=[materials[item.material]!]
            let node=SCNNode(geometry:b);node.name=item.name;node.simdPosition=vec(item.position)
            node.categoryBitMask=1;node.castsShadow=item.group != "lights"
            scene.rootNode.addChildNode(node)
            if item.group=="shutter" {shutters.append(node);node.isHidden=true}
            if item.group=="door" {doors.append(node)}
            if item.collision && item.position[1]<1.8 && item.position[1]+Float(item.size[1])/2>0.12 { obstacles.append(item) }
        }
        // Small service graphics are geometry, so the game never relies on raster UI lettering.
        label("ORBITAL / 01",at:SIMD3(-0.61,2.47,3.728),size:0.10,angle:.pi)
        label("CREW QUARTERS",at:SIMD3(-0.53,2.30,3.727),size:0.045,angle:.pi)
        label("COMMON",at:SIMD3(-0.29,2.35,7.806),size:0.055,angle:.pi)
        label("EARTH OBSERVATION",at:SIMD3(-2.36,0.39,-3.889),size:0.035,angle:0)
        label("01  /  A. REYES",at:SIMD3(-2.99,1.57,0.32),size:0.055,angle:Float.pi/2)
        // Personal touches: mug, books, framed photo, cloth folds.
        let mug=SCNCylinder(radius:0.037,height:0.10);mug.materials=[materials["metal"]!]
        let mn=SCNNode(geometry:mug);mn.position=SCNVector3(2.04,0.92,-1.17);scene.rootNode.addChildNode(mn)
        let ring=SCNTorus(ringRadius:0.033,pipeRadius:0.007);ring.materials=[materials["metal"]!]
        let rn=SCNNode(geometry:ring);rn.position=SCNVector3(2.085,0.92,-1.17);rn.eulerAngles.x = .pi/2;scene.rootNode.addChildNode(rn)
        for i in 0..<18 {
            let fold=SCNBox(width:1.22,height:0.011,length:0.018,chamferRadius:0.005);fold.materials=[materials["fabric"]!]
            let n=SCNNode(geometry:fold);n.simdPosition=SIMD3(-2.43,0.886,-1.90+Float(i)*0.08);n.simdEulerAngles.y=sin(Float(i)*2.3)*0.025;scene.rootNode.addChildNode(n)
        }
        let frame=SCNBox(width:0.018,height:0.29,length:0.41,chamferRadius:0.01);frame.materials=[materials["graphite"]!]
        let fn=SCNNode(geometry:frame);fn.position=SCNVector3(-3.12,1.44,-1.80);scene.rootNode.addChildNode(fn)
        let photo=SCNPlane(width:0.37,height:0.25);let pm=SCNMaterial();pm.diffuse.contents=texture("earth-day.jpg");pm.lightingModel = .constant;photo.materials=[pm]
        let pn=SCNNode(geometry:photo);pn.position=SCNVector3(-3.105,1.44,-1.8);pn.eulerAngles.y = .pi/2;scene.rootNode.addChildNode(pn)
    }
    func label(_ text:String,at p:SIMD3<Float>,size:CGFloat,angle:Float) {
        let t=SCNText(string:text,extrusionDepth:0.001);t.font=NSFont.monospacedSystemFont(ofSize:1,weight:.medium)
        t.flatness=0.4;let m=SCNMaterial();m.diffuse.contents=NSColor(white:0.55,alpha:1);m.lightingModel = .constant;t.materials=[m]
        let n=SCNNode(geometry:t);n.simdPosition=p;n.simdScale=SIMD3(repeating:Float(size));n.simdEulerAngles.y=angle
        scene.rootNode.addChildNode(n)
    }
    func buildEarth() {
        let sphere=SCNSphere(radius:layout.earth.radius);sphere.segmentCount=192
        earthMaterial.lightingModel = .physicallyBased
        earthMaterial.diffuse.contents=texture("earth-day.jpg")
        if usesExistingCabin,let day=texture("earth16-day.jpg") {
            earthMaterial.diffuse.contents=day
            earthMaterial.normal.contents=texture("earth16-normal.jpg")
        }
        earthMaterial.roughness.contents=0.85;earthMaterial.metalness.contents=0.0
        if usesExistingCabin,let rough=texture("earth16-roughness.jpg") {earthMaterial.roughness.contents=rough;earthMaterial.roughness.textureComponents = .red}
        earthMaterial.emission.contents=NSColor.black;earthMaterial.emission.intensity=0
        sphere.materials=[earthMaterial];earth.geometry=sphere
        earth.simdPosition=vec(layout.earth.position);earth.eulerAngles.x = 0.75;earth.eulerAngles.y = 1.85;earth.eulerAngles.z = -0.08
        if usesExistingCabin {earth.simdPosition=SIMD3(1600,-3300,-6100)}
        earth.categoryBitMask=2;earth.castsShadow=false;scene.rootNode.addChildNode(earth)
        let clouds=SCNSphere(radius:layout.earth.radius+8);clouds.segmentCount=192
        let cm=SCNMaterial();cm.diffuse.contents=NSColor.white;cm.roughness.contents=1;cm.metalness.contents=0
        cm.diffuse.contents=texture(usesExistingCabin ? "earth16-clouds-alpha.png" : "earth-clouds-alpha.png") ?? texture("earth-clouds-alpha.png");cm.transparencyMode = .aOne;cm.blendMode = .alpha
        cm.writesToDepthBuffer=false;clouds.materials=[cm]
        let cn=SCNNode(geometry:clouds);cn.categoryBitMask=2;cn.castsShadow=false;cn.renderingOrder=10;earth.addChildNode(cn)
        let atmosphere=SCNSphere(radius:layout.earth.radius+34);atmosphere.segmentCount=192
        let am=SCNMaterial();am.lightingModel = .constant;am.diffuse.contents=NSColor(calibratedRed:0.12,green:0.40,blue:0.95,alpha:1)
        am.blendMode = .add;am.writesToDepthBuffer=false;am.transparency=0.22
        am.shaderModifiers=[.surface:"""
        float facing = abs(dot(normalize(_surface.normal), normalize(_surface.view)));
        _surface.transparent.a = pow(1.0 - facing, 5.0) * 0.55;
        """]
        atmosphere.materials=[am];let an=SCNNode(geometry:atmosphere);an.categoryBitMask=2;an.renderingOrder=20;an.castsShadow=false;earth.addChildNode(an)
        let sky=SCNSphere(radius:24000);sky.segmentCount=64
        let sm=SCNMaterial();sm.diffuse.contents=texture("stars-milky-way.jpg");sm.lightingModel = .constant;sm.cullMode = .front
        sm.writesToDepthBuffer=false;sm.diffuse.intensity=0.018;sky.materials=[sm]
        let sn=SCNNode(geometry:sky);sn.categoryBitMask=2;sn.castsShadow=false;sn.renderingOrder = -100;sn.eulerAngles.z = 0.5
        scene.rootNode.addChildNode(sn);stars=sn
    }
    func buildLighting() {
        let sl=SCNLight();sl.type = .directional;sl.intensity=700;sl.color=NSColor(calibratedRed:1,green:0.97,blue:0.92,alpha:1)
        sl.categoryBitMask=1 | 4
        sl.castsShadow=true;sl.shadowMode = .deferred;sl.shadowMapSize=CGSize(width:2048,height:2048)
        sl.shadowSampleCount=16;sl.shadowRadius=2;sl.orthographicScale=12;sl.zNear=0.1;sl.zFar=20000
        sl.shadowColor=NSColor(white:0,alpha:0.70);sun.light=sl
        sun.eulerAngles=SCNVector3(-0.64,-0.48,0);scene.rootNode.addChildNode(sun)
        let earthSun=SCNLight();earthSun.type = .directional;earthSun.intensity=1100
        earthSun.categoryBitMask=2;earthSun.color=NSColor.white
        let es=SCNNode();es.name="earth-sun";es.light=earthSun;es.eulerAngles=SCNVector3(-0.3,-0.35,0)
        scene.rootNode.addChildNode(es)
        let al=SCNLight();al.type = .ambient;al.intensity=55;al.color=NSColor(calibratedRed:0.69,green:0.77,blue:0.88,alpha:1)
        ambient.light=al;scene.rootNode.addChildNode(ambient)
        for p in [SIMD3<Float>(0,2.5,-2.7),SIMD3(0,2.5,0),SIMD3(0,2.5,2.6),SIMD3(0,2.4,6),SIMD3(0,2.5,10.3)] {
            let l=SCNLight();l.type = .omni;l.intensity=90;l.color=NSColor(calibratedRed:1,green:0.86,blue:0.68,alpha:1)
            l.attenuationStartDistance=0.5;l.attenuationEndDistance=5.5
            let n=SCNNode();n.light=l;n.simdPosition=p;scene.rootNode.addChildNode(n);lamps.append(n)
        }
        let earthBounce=SCNLight();earthBounce.type = .omni;earthBounce.intensity=60
        earthBounce.color=NSColor(calibratedRed:0.40,green:0.64,blue:1,alpha:1)
        earthBounce.attenuationEndDistance=8;let en=SCNNode();en.light=earthBounce;en.position=SCNVector3(0,2,-3.7);scene.rootNode.addChildNode(en)
    }
    func buildCharacter() {
        scene.rootNode.addChildNode(player);player.simdPosition=vec(layout.spawn)
        do {
            character=try GLBCharacter(url:assetURL.appendingPathComponent("Source/Crew.glb"),textures:assetURL.appendingPathComponent("Textures"))
            let n=character!.root;n.name="crew-proxy";n.eulerAngles.y = .pi
            n.enumerateChildNodes { c,_ in c.categoryBitMask=4 }
            player.addChildNode(n)
        } catch {
            NSLog("Character failed: %@",String(describing:error))
        }
    }
    func buildCamera() {
        let c=SCNCamera();c.fieldOfView=68;c.zNear=0.045;c.zFar=60000
        c.wantsHDR=true;c.wantsExposureAdaptation=false;c.minimumExposure = -2;c.maximumExposure=0
        c.exposureOffset = -0.8;c.bloomIntensity=0.06;c.bloomThreshold=1.0
        c.wantsDepthOfField=false;c.screenSpaceAmbientOcclusionIntensity=0.65
        c.screenSpaceAmbientOcclusionRadius=0.35;c.screenSpaceAmbientOcclusionBias=0.025
        camera.camera=c;scene.rootNode.addChildNode(camera);view.pointOfView=camera
    }
    func buildOverlay() {
        let title=NSTextField(labelWithString:"ORBITAL HABITAT")
        title.font=NSFont.monospacedSystemFont(ofSize:13,weight:.medium);title.textColor=NSColor(white:0.88,alpha:1)
        let subtitle=NSTextField(labelWithString:"EARTH ORBIT   /   CREW QUARTERS")
        subtitle.font=NSFont.monospacedSystemFont(ofSize:10,weight:.regular);subtitle.textColor=NSColor(white:0.62,alpha:1)
        for label in [title,subtitle,status,prompt,mode] {label.translatesAutoresizingMaskIntoConstraints=false;view.addSubview(label)}
        for label in [status,prompt,mode] {label.font=NSFont.monospacedSystemFont(ofSize:11,weight:.regular);label.textColor=NSColor(white:0.83,alpha:1)}
        status.stringValue="WASD MOVE  ·  CLICK / DRAG LOOK  ·  V CAMERA  ·  ESC CURSOR"
        mode.stringValue=usesExistingCabin ? "L LIGHTS · N NIGHT · Q QUALITY · P STATS · R RESET · H HIDE CONTROLS" : "E DOOR · L LIGHTS · O SHUTTER · N NIGHT · P STATS"
        NSLayoutConstraint.activate([
            title.leadingAnchor.constraint(equalTo:view.leadingAnchor,constant:28),title.topAnchor.constraint(equalTo:view.topAnchor,constant:25),
            subtitle.leadingAnchor.constraint(equalTo:title.leadingAnchor),subtitle.topAnchor.constraint(equalTo:title.bottomAnchor,constant:5),
            status.leadingAnchor.constraint(equalTo:view.leadingAnchor,constant:28),status.bottomAnchor.constraint(equalTo:view.bottomAnchor,constant:-24),
            mode.leadingAnchor.constraint(equalTo:status.leadingAnchor),mode.bottomAnchor.constraint(equalTo:status.topAnchor,constant:-7),
            prompt.centerXAnchor.constraint(equalTo:view.centerXAnchor),prompt.bottomAnchor.constraint(equalTo:mode.topAnchor,constant:-26)])
    }
    func start() {
        lastTime=CACurrentMediaTime()
        timer=Timer.scheduledTimer(withTimeInterval:1.0/60,repeats:true) { [weak self] _ in self?.tick() }
        RunLoop.main.add(timer!,forMode:.common)
    }
    func key(_ code:UInt16,down:Bool,repeatKey:Bool) {
        if down {pressed.insert(code)} else {pressed.remove(code)}
        guard down && !repeatKey else {return}
        switch code {
        case 53:releaseMouse()
        case 14:interact()
        case 37:toggleLights()
        case 31:toggleShutter()
        case 45:toggleNight()
        case 9:thirdPerson.toggle()
        case 12:toggleQuality()
        case 35:view.showsStatistics.toggle()
        case 15:player.simdPosition=vec(layout.spawn);yaw=0;pitch = -0.04
        case 4:for v in view.subviews {v.isHidden.toggle()}
        default:break
        }
    }
    func captureMouse() {
        guard !mouseCaptured else {return};mouseCaptured=true;NSCursor.hide();CGAssociateMouseAndMouseCursorPosition(0)
        view.window?.makeFirstResponder(view)
    }
    func releaseMouse() {if mouseCaptured {mouseCaptured=false;NSCursor.unhide();CGAssociateMouseAndMouseCursorPosition(1)};pressed.removeAll();sprint=false}
    func look(dx:Float,dy:Float) {yaw -= dx*0.0025;pitch=max(-1.1,min(1.1,pitch-dy*0.0025))}
    func toggleLights() {lightsOn.toggle()}
    func toggleShutter() {
        shutterClosed.toggle()
        for n in shutters {
            n.isHidden=false
            SCNTransaction.begin();SCNTransaction.animationDuration=0.75
            n.position.y=shutterClosed ? 1.68 : 3.30
            SCNTransaction.commit()
        }
    }
    func toggleNight() {
        night.toggle()
        SCNTransaction.begin();SCNTransaction.animationDuration=2
        sun.light?.intensity=night ? 20 : 700
        ambient.light?.intensity=night ? 20 : 55
        earthMaterial.emission.contents=night ? (texture(usesExistingCabin ? "earth16-night.jpg" : "earth-night.jpg") ?? texture("earth-night.jpg")) : NSColor.black
        earthMaterial.emission.intensity=night ? 0.9 : 0
        if let es=scene.rootNode.childNode(withName:"earth-sun",recursively:false) {
            es.light?.intensity=night ? 25 : 1100
            es.eulerAngles.y=night ? 2.8 : -0.35
        }
        sun.eulerAngles.y=night ? 2.8 : -0.48
        SCNTransaction.commit()
    }
    func toggleQuality() {
        highQuality.toggle();view.antialiasingMode=highQuality ? .multisampling4X : .none
        camera.camera?.screenSpaceAmbientOcclusionIntensity=highQuality ? 0.65 : 0
        sun.light?.shadowMapSize=CGSize(width:highQuality ? 2048 : 1024,height:highQuality ? 2048 : 1024)
    }
    func interact() {
        let d=simd_distance(player.simdPosition,SIMD3<Float>(0,0,3.86))
        if d<2.0 {
            doorOpen.toggle();SCNTransaction.begin();SCNTransaction.animationDuration=0.6
            for n in doors {n.position.x=doorOpen ? -1.40 : 0};SCNTransaction.commit()
        } else if player.position.z < -2.1 { toggleLights() }
    }
    func validPosition(_ p:SIMD3<Float>)->Bool {
        let r:Float=0.24
        guard layout.roomBounds.contains(where:{p.x>$0[0]+r && p.x<$0[1]-r && p.z>$0[2] && p.z<$0[3]}) else {return false}
        for o in obstacles {
            if o.group=="door" && doorOpen {continue}
            let x=o.position[0],z=o.position[2],w=Float(o.size[0])*0.5+r,d=Float(o.size[2])*0.5+r
            if abs(p.x-x)<w && abs(p.z-z)<d {return false}
        }
        return true
    }
    func tick() {
        let now=CACurrentMediaTime();let dt=Float(min(0.05,now-lastTime));lastTime=now;clock += Double(dt)
        var move=SIMD2<Float>(0,0)
        if pressed.contains(13) || pressed.contains(126) {move.y -= 1}
        if pressed.contains(1) || pressed.contains(125) {move.y += 1}
        if pressed.contains(0) || pressed.contains(123) {move.x -= 1}
        if pressed.contains(2) || pressed.contains(124) {move.x += 1}
        var speed:Float=0
        if simd_length(move)>0 {
            move=simd_normalize(move);speed=sprint ? 2.7 : 1.5
            let offset=SIMD3<Float>(cos(yaw)*move.x+sin(yaw)*move.y,0,-sin(yaw)*move.x+cos(yaw)*move.y)*speed*dt
            var p=player.simdPosition
            let nx=SIMD3(p.x+offset.x,p.y,p.z);if validPosition(nx) {p=nx}
            let nz=SIMD3(p.x,p.y,p.z+offset.z);if validPosition(nz) {p=nz}
            player.simdPosition=p
        }
        player.simdEulerAngles.y=yaw
        character?.animate(delta:dt,speed:speed)
        let desired:CGFloat=lightsOn ? 1 : 0.10;lightLevel += (desired-lightLevel)*CGFloat(min(dt*4,1))
        for l in lamps {l.light?.intensity=90*lightLevel}
        materials["light"]?.emission.intensity=0.8*lightLevel
        let lookAwayFromEarth = camera.worldFront.y > 0.12 || camera.worldFront.z > 0.20
        let target:CGFloat=night && !lightsOn && lookAwayFromEarth ? 0.72 : (night && !lightsOn ? 0.16 : 0.006)
        starLevel += (target-starLevel)*CGFloat(min(dt*0.7,1));stars?.geometry?.firstMaterial?.diffuse.intensity=starLevel
        earth.simdEulerAngles.y += dt*0.00018
        updateCamera(delta:dt,speed:speed)
        let d=simd_distance(player.simdPosition,SIMD3<Float>(0,0,3.86))
        prompt.stringValue=usesExistingCabin ? "" : (d<2 ? (doorOpen ? "E  CLOSE CABIN DOOR" : "E  OPEN CABIN DOOR") : (player.position.z < -2.1 ? "E  TOGGLE OBSERVATION LIGHTING" : ""))
        let room=player.position.z>7.9 ? "COMMON ROOM" : (player.position.z>3.7 ? "PASSAGE" : "CREW QUARTERS")
        status.stringValue="\(room)   ·   \(thirdPerson ? "THIRD PERSON" : "FIRST PERSON")   ·   \(night ? "NIGHT" : "DAY")   ·   \(highQuality ? "HIGH" : "BALANCED")"
    }
    func updateCamera(delta:Float,speed:Float) {
        let direction=SIMD3<Float>(-sin(yaw)*cos(pitch),sin(pitch),-cos(yaw)*cos(pitch))
        let pivot=player.simdPosition+SIMD3(0,1.50,0)
        if thirdPerson {
            character?.setFirstPerson(false)
            var desired=pivot-direction*cameraDistance+SIMD3(cos(yaw)*0.32,0.15,-sin(yaw)*0.32)
            let hits=scene.rootNode.hitTestWithSegment(from:SCNVector3(pivot),to:SCNVector3(desired),options:[SCNHitTestOption.categoryBitMask.rawValue:1,SCNHitTestOption.backFaceCulling.rawValue:false])
            if let hit=hits.min(by:{simd_distance(pivot,SIMD3($0.worldCoordinates))<simd_distance(pivot,SIMD3($1.worldCoordinates))}) {
                let h=SIMD3<Float>(hit.worldCoordinates);desired=h+simd_normalize(pivot-h)*0.15
            }
            camera.simdPosition=desired
            camera.look(at:SCNVector3(pivot+direction*3),up:SCNVector3(0,1,0),localFront:SCNVector3(0,0,-1))
        } else {
            character?.setFirstPerson(true)
            bob += delta*speed*5
            camera.simdPosition=player.simdPosition+SIMD3(0,1.58+(speed>0 ? sin(bob)*0.012 : 0),0)
            camera.look(at:SCNVector3(camera.simdPosition+direction),up:SCNVector3(0,1,0),localFront:SCNVector3(0,0,-1))
        }
    }
    func save() {
        guard !CommandLine.arguments.contains("--snapshot") else {return}
        try? FileManager.default.createDirectory(at:stateURL.deletingLastPathComponent(),withIntermediateDirectories:true)
        let p=player.simdPosition
        if let data=try? JSONSerialization.data(withJSONObject:["build":usesExistingCabin ? 3 : 2,"position":[p.x,p.y,p.z],"yaw":yaw],options:.prettyPrinted) {try? data.write(to:stateURL)}
    }
    func verifyInteractions()->Bool {
        let oldPosition=player.simdPosition
        player.simdPosition=SIMD3(0,0,3.2)
        let closedBlocks = !validPosition(SIMD3(0,0,3.86))
        interact()
        let route=(0...24).allSatisfy {validPosition(SIMD3(0,0,3.3+Float($0)*0.22))}
        let furnitureBlocks = !validPosition(SIMD3(-2.43,0,-1.6))
        interact();player.simdPosition=oldPosition
        toggleLights();let dimmed = !lightsOn;toggleLights()
        toggleShutter();let closed=shutterClosed;toggleShutter()
        let ok=closedBlocks && route && furnitureBlocks && dimmed && closed
        print("INTERACTIONS_\(ok ? "OK" : "FAILED") doorBlocks=\(closedBlocks) routeToCommon=\(route) furnitureBlocks=\(furnitureBlocks) lights=\(dimmed) shutter=\(closed)")
        return ok
    }
}

final class AppDelegate:NSObject,NSApplicationDelegate,NSWindowDelegate {
    var window:NSWindow!,game:Habitat!
    func applicationDidFinishLaunching(_ notification:Notification) {
        let appDir=Bundle.main.bundleURL.deletingLastPathComponent()
        let args=CommandLine.arguments
        let assets:URL
        if let i=args.firstIndex(of:"--assets"),args.count>i+1 {assets=URL(fileURLWithPath:args[i+1])}
        else if let resources=Bundle.main.resourceURL,FileManager.default.fileExists(atPath:resources.appendingPathComponent("Assets/layout.json").path) {assets=resources.appendingPathComponent("Assets")}
        else {assets=appDir.appendingPathComponent("Assets")}
        window=NSWindow(contentRect:NSRect(x:0,y:0,width:1440,height:900),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title="Orbital Habitat — Native Preview";window.backgroundColor = .black
        window.minSize=NSSize(width:960,height:640);window.center();window.delegate=self
        let view=GameView(frame:window.contentView!.bounds,options:[SCNView.Option.preferredRenderingAPI.rawValue:SCNRenderingAPI.metal.rawValue])
        view.autoresizingMask=[.width,.height];window.contentView=view
        do {game=try Habitat(view:view,assets:assets)}
        catch {NSLog("Could not load habitat: %@",String(describing:error));NSApp.terminate(nil);return}
        window.makeKeyAndOrderFront(nil);window.makeFirstResponder(view);window.acceptsMouseMovedEvents=true
        NSApp.activate(ignoringOtherApps:true)
        if args.contains("--smoke-check") {
            let visible=game.scene.rootNode.childNodes.filter{!$0.isHidden}.count
            print("SCENE_OK objects=\(visible) character=\(game.character != nil) assets=\(assets.path)")
            guard game.verifyInteractions() else {NSApp.terminate(nil);return}
        }
        game.start()
        if let i=args.firstIndex(of:"--snapshot"),args.count>i+1 {
            let path=args[i+1]
            DispatchQueue.main.asyncAfter(deadline:.now()+2.5) {
                let image=view.snapshot()
                guard let tiff=image.tiffRepresentation,let bitmap=NSBitmapImageRep(data:tiff),let png=bitmap.representation(using:.png,properties:[:]) else {return}
                try? png.write(to:URL(fileURLWithPath:path));print("SNAPSHOT_OK \(path)")
                if args.contains("--exit-after-snapshot") {NSApp.terminate(nil)}
            }
        }
    }
    func applicationDidResignActive(_ notification:Notification) {game?.releaseMouse()}
    func applicationWillTerminate(_ notification:Notification) {game?.releaseMouse();game?.save()}
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool {true}
    func windowWillClose(_ notification:Notification) {game?.releaseMouse();game?.save()}
}

@main enum HabitatEntry {
    static func main() {
        let app=NSApplication.shared
        app.setActivationPolicy(.regular)
        let delegate=AppDelegate();app.delegate=delegate
        let menu=NSMenu();let appItem=NSMenuItem();menu.addItem(appItem)
        let appMenu=NSMenu();appMenu.addItem(withTitle:"Quit Orbital Habitat",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q");appItem.submenu=appMenu
        let viewItem=NSMenuItem(title:"View",action:nil,keyEquivalent:"");let viewMenu=NSMenu()
        viewMenu.addItem(withTitle:"Enter Full Screen",action:#selector(NSWindow.toggleFullScreen(_:)),keyEquivalent:"f");viewItem.submenu=viewMenu;menu.addItem(viewItem)
        app.mainMenu=menu
        withExtendedLifetime(delegate) { app.run() }
    }
}
