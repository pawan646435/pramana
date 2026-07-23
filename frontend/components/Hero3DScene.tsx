"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { useIsCoarsePointer } from "@/lib/useIsCoarsePointer";

interface Fact {
  name: string;
  text: string;
}

const FACTS: Record<string, Fact> = {
  Sun: { name: "Surya", text: "The Sun's sign, the Surya Rashi, anchors the soul and sense of self in Vedic astrology." },
  Mercury: { name: "Budha", text: "Mercury governs communication and intellect — its retrograde periods are computed, not guessed, from real orbital data." },
  Venus: { name: "Shukra", text: "Venus rules relationships and beauty; its dasha periods can span two decades of a life." },
  Mars: { name: "Mangala", text: "Mars in the 7th house is a classical placement studied for its effect on partnerships and conflict." },
  Jupiter: { name: "Guru", text: "Jupiter's transit through a house is tracked over roughly a 12-year cycle, one house per year." },
  Saturn: { name: "Shani", text: "Saturn's sade-sati, a 7.5 year transit period, is computed exactly from its real orbital position." },
  Moon: { name: "Chandra", text: "The Moon's nakshatra changes roughly every day, computed precisely from its actual position." },
};

const PLANET_DEFS = [
  { name: "Mercury", color: [150, 145, 140] as [number, number, number], size: 0.6, dist: 8, speed: 0.9, spin: 0.003 },
  { name: "Venus", color: [223, 204, 158] as [number, number, number], size: 1.0, dist: 12, speed: 0.65, spin: 0.0015 },
  { name: "Mars", color: [193, 98, 68] as [number, number, number], size: 0.75, dist: 16.5, speed: 0.5, spin: 0.0045 },
  { name: "Jupiter", color: [223, 200, 165] as [number, number, number], size: 2.2, dist: 23, speed: 0.32, spin: 0.009, moons: 2 },
  { name: "Saturn", color: [222, 200, 150] as [number, number, number], size: 1.9, dist: 29, speed: 0.22, spin: 0.007, ring: true, moons: 1 },
  { name: "Moon", color: [225, 223, 222] as [number, number, number], size: 0.4, dist: 35, speed: 0.75, spin: 0.0025 },
];

export default function Hero3DScene() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredFact, setHoveredFact] = useState<Fact | null>(null);
  const [hoveredLabel, setHoveredLabel] = useState<string>("");
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isPointerOverPlanet, setIsPointerOverPlanet] = useState(false);
  const isCoarsePointer = useIsCoarsePointer();

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();

    // On narrow/portrait viewports (aspect < 1, e.g. a phone) the same
    // FOV + distance that frames the scene nicely on a landscape/desktop
    // aspect ratio crops the orbit ring on the sides. Widening the FOV
    // and pulling the camera back as aspect ratio drops keeps the full
    // solar system visible and centered instead of feeling zoomed in.
    function cameraSetupForAspect(aspect: number): { fov: number; distance: number } {
      if (aspect >= 1) return { fov: 50, distance: 54 };
      const t = Math.min(1, (1 - aspect) / 0.7); // 0 at aspect=1, 1 at aspect<=0.3
      return { fov: 50 + t * 22, distance: 54 + t * 26 };
    }

    const initialAspect = window.innerWidth / window.innerHeight;
    const initialSetup = cameraSetupForAspect(initialAspect);
    const camera = new THREE.PerspectiveCamera(initialSetup.fov, initialAspect, 0.1, 1000);
    // True center - the earlier left/right offset didn't read as centered
    // in practice. Layout now solves the text-overlap problem by giving
    // the page real scroll height instead of fighting for the same frame.
    camera.position.set(0, 26, initialSetup.distance);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Moderate indigo ambient plus a strong sun point light still produces
    // a visible day/night terminator, but keeps the unlit side dim and
    // moody rather than pure black. A cool fill light opposite the sun
    // adds a faint rim on the dark side (starlight / atmospheric scatter).
    scene.add(new THREE.AmbientLight(0x2a2850, 0.4));
    // decay=0 (no physical falloff) because orbit radii span 8-35 units -
    // with realistic decay the sun light was crushed to near-nothing by
    // the time it reached Jupiter/Saturn/Moon, leaving them looking flat
    // black. `distance` still caps its reach.
    const sunLight = new THREE.PointLight(0xfff0d0, 2.4, 500, 0);
    scene.add(sunLight);
    const rimLight = new THREE.PointLight(0x6f6bb0, 0.5, 200);
    rimLight.position.set(-30, 20, -30);
    scene.add(rimLight);
    const fillLight = new THREE.PointLight(0x4a5a8a, 0.35, 250);
    fillLight.position.set(40, -15, 40);
    scene.add(fillLight);

    // Starfield
    const starGeo = new THREE.BufferGeometry();
    const starCount = 1600;
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const r = 200 + Math.random() * 300;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      starPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      starPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      starPositions[i * 3 + 2] = r * Math.cos(phi);
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.7, transparent: true, opacity: 0.8 });
    scene.add(new THREE.Points(starGeo, starMat));

    // Higher-resolution procedural textures with layered detail - craters
    // and albedo variation for rocky bodies, turbulent banding for gas
    // giants - so surfaces read as real terrain rather than flat color.
    function makeTexture(baseColor: [number, number, number], style: "rocky" | "bands"): THREE.CanvasTexture {
      const size = 512;
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size / 2;
      const ctx = canvas.getContext("2d")!;
      const [r, g, b] = baseColor;

      if (style === "bands") {
        const bandCount = 8 + Math.floor(Math.random() * 5);
        for (let y = 0; y < canvas.height; y++) {
          const t1 = Math.sin((y / canvas.height) * Math.PI * bandCount);
          const t2 = Math.sin((y / canvas.height) * Math.PI * bandCount * 2.3 + 1.5) * 0.3;
          const mix = 0.35 + ((t1 + t2 + 1) / 2) * 0.45;
          const cr = Math.min(255, r + (255 - r) * mix * 0.4);
          const cg = Math.min(255, g + (255 - g) * mix * 0.4);
          const cb = Math.min(255, b + (255 - b) * mix * 0.4);
          ctx.fillStyle = `rgb(${cr},${cg},${cb})`;
          ctx.fillRect(0, y, canvas.width, 1);
        }
        for (let i = 0; i < 500; i++) {
          const x = Math.random() * canvas.width;
          const y = Math.random() * canvas.height;
          const w = 30 + Math.random() * 90;
          const h = 1 + Math.random() * 3;
          ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.06})`;
          ctx.fillRect(x, y, w, h);
        }
      } else {
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < 2500; i++) {
          const x = Math.random() * canvas.width;
          const y = Math.random() * canvas.height;
          const rad = 0.5 + Math.random() * 2;
          const shade = Math.random() > 0.5 ? "255,255,255" : "0,0,0";
          ctx.fillStyle = `rgba(${shade},${Math.random() * 0.08})`;
          ctx.beginPath();
          ctx.arc(x, y, rad, 0, Math.PI * 2);
          ctx.fill();
        }
        for (let i = 0; i < 45; i++) {
          const x = Math.random() * canvas.width;
          const y = Math.random() * canvas.height;
          const rad = 3 + Math.random() * 10;
          const grad = ctx.createRadialGradient(x, y, 0, x, y, rad);
          grad.addColorStop(0, "rgba(0,0,0,0.35)");
          grad.addColorStop(0.7, "rgba(0,0,0,0.15)");
          grad.addColorStop(0.85, "rgba(255,255,255,0.12)");
          grad.addColorStop(1, "rgba(0,0,0,0)");
          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.arc(x, y, rad, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      const tex = new THREE.CanvasTexture(canvas);
      tex.needsUpdate = true;
      tex.anisotropy = 4;
      return tex;
    }

    // Radial ring texture with concentric banding and gaps (e.g. the
    // Cassini Division) rather than a flat solid color.
    function makeRingTexture(baseColor: [number, number, number]): THREE.CanvasTexture {
      const size = 512;
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = 64;
      const ctx = canvas.getContext("2d")!;
      const [r, g, b] = baseColor;
      // x axis maps to ring radius (inner -> outer)
      for (let x = 0; x < canvas.width; x++) {
        const t = x / canvas.width;
        const band = Math.sin(t * Math.PI * 22) * 0.5 + 0.5;
        const gapMask =
          (t > 0.42 && t < 0.47) || (t > 0.66 && t < 0.69) ? 0.15 : 1;
        const shade = 0.55 + band * 0.45;
        const alpha = (0.35 + shade * 0.5) * gapMask * (0.4 + t * 0.4);
        ctx.fillStyle = `rgba(${Math.min(255, r * shade)},${Math.min(255, g * shade)},${Math.min(255, b * shade)},${alpha})`;
        ctx.fillRect(x, 0, 1, canvas.height);
      }
      const tex = new THREE.CanvasTexture(canvas);
      tex.needsUpdate = true;
      return tex;
    }

    const sun = new THREE.Mesh(
      new THREE.SphereGeometry(3.6, 48, 48),
      new THREE.MeshBasicMaterial({ map: makeTexture([255, 224, 130], "rocky") })
    );
    sun.userData = { label: "Sun", isSun: true };
    scene.add(sun);
    sunLight.position.copy(sun.position);

    [4.0, 4.7, 5.8].forEach((r, i) => {
      const glow = new THREE.Mesh(
        new THREE.SphereGeometry(r, 32, 32),
        new THREE.MeshBasicMaterial({
          color: 0xffdca0,
          transparent: true,
          opacity: [0.28, 0.14, 0.06][i],
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        })
      );
      scene.add(glow);
    });

    const planets: THREE.Mesh[] = [];
    PLANET_DEFS.forEach((def) => {
      const ringGeo = new THREE.RingGeometry(def.dist - 0.02, def.dist + 0.02, 128);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.06, side: THREE.DoubleSide });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2;
      scene.add(ringMesh);

      const style: "rocky" | "bands" = ["Venus", "Jupiter", "Saturn"].includes(def.name) ? "bands" : "rocky";
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(def.size, 48, 48),
        new THREE.MeshStandardMaterial({
          map: makeTexture(def.color, style),
          roughness: style === "bands" ? 0.55 : 0.85,
          metalness: style === "bands" ? 0.15 : 0.05,
        })
      );
      mesh.userData = {
        label: def.name,
        dist: def.dist,
        speed: def.speed,
        spin: def.spin,
        angle: Math.random() * Math.PI * 2,
        isPlanet: true,
      };
      scene.add(mesh);
      planets.push(mesh);

      const atmoColor = new THREE.Color(def.color[0] / 255, def.color[1] / 255, def.color[2] / 255);
      const atmosphere = new THREE.Mesh(
        new THREE.SphereGeometry(def.size * 1.12, 32, 32),
        new THREE.MeshBasicMaterial({ color: atmoColor, transparent: true, opacity: 0.12, side: THREE.BackSide })
      );
      mesh.add(atmosphere);

      if (def.ring) {
        const saturnRing = new THREE.Mesh(
          new THREE.RingGeometry(def.size * 1.3, def.size * 2.0, 128, 1),
          new THREE.MeshBasicMaterial({
            map: makeRingTexture(def.color),
            transparent: true,
            side: THREE.DoubleSide,
            depthWrite: false,
          })
        );
        // Tilt from the orbital plane; RingGeometry is built flat on XY so
        // a base -90deg X rotation lays it flat, then we tilt it further.
        saturnRing.rotation.x = -Math.PI / 2 + THREE.MathUtils.degToRad(24);
        mesh.add(saturnRing);
      }

      const moonCount = def.moons ?? 0;
      for (let i = 0; i < moonCount; i++) {
        const moonDist = def.size * (1.7 + i * 0.55);
        const tinyMoon = new THREE.Mesh(
          new THREE.SphereGeometry(def.size * 0.09, 12, 12),
          new THREE.MeshBasicMaterial({ color: 0xffffff })
        );
        tinyMoon.userData = {
          isMoonlet: true,
          dist: moonDist,
          speed: 1.8 + i * 0.6,
          angle: Math.random() * Math.PI * 2,
        };
        mesh.add(tinyMoon);
      }
    });

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    // THREE.Vector2's default (0,0) is screen-CENTER in NDC space, i.e.
    // exactly where the Sun sits - without this flag, the very first
    // animate() frame (before any real pointer event has ever fired)
    // raycasts against that stale center point and shows the Sun's fact
    // card unprompted, before the user has touched or moved anything.
    let hasRealPointerPosition = false;
    let hoveredMesh: THREE.Object3D | null = null;
    let draggedPlanet: THREE.Mesh | null = null;
    const dragPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const dragIntersection = new THREE.Vector3();

    // Touch has no hover state, so tap-to-reveal replaces hover-to-reveal:
    // a tap (pointerdown+pointerup on the same spot, not a drag) on a
    // planet pins its fact card open until the user taps elsewhere. These
    // track that gesture and the manual scroll-passthrough described below.
    let pointerDownClientY = 0;
    let touchMoved = false;
    const TOUCH_MOVE_THRESHOLD = 8; // px - beyond this, a touch is a drag/scroll, not a tap
    let isScrollingPage = false;
    let lastScrollTouchY = 0;
    let lastPointerWasTouch = false;

    function updateMouseFromEvent(e: PointerEvent) {
      hasRealPointerPosition = true;
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    }

    function onPointerMove(e: PointerEvent) {
      lastPointerWasTouch = e.pointerType === "touch";
      updateMouseFromEvent(e);
      if (e.pointerType !== "touch") {
        setCursorPos({ x: e.clientX, y: e.clientY });
      }

      if (Math.abs(e.clientY - pointerDownClientY) > TOUCH_MOVE_THRESHOLD) {
        touchMoved = true;
      }

      if (draggedPlanet) {
        e.preventDefault();
        raycaster.setFromCamera(mouse, camera);
        if (raycaster.ray.intersectPlane(dragPlane, dragIntersection)) {
          const angle = Math.atan2(dragIntersection.z, dragIntersection.x);
          draggedPlanet.userData.angle = angle;
        }
      } else if (e.pointerType === "touch" && isScrollingPage) {
        // The canvas has touch-action: none (needed so a planet drag never
        // triggers the browser's native pan/zoom mid-gesture), which also
        // suppresses native scrolling everywhere on the canvas - including
        // over empty space. Reimplementing scroll manually here is what
        // keeps "touch empty space to scroll the page" working.
        const delta = lastScrollTouchY - e.clientY;
        window.scrollBy(0, delta);
        lastScrollTouchY = e.clientY;
      }
    }

    function onPointerDown(e: PointerEvent) {
      lastPointerWasTouch = e.pointerType === "touch";
      pointerDownClientY = e.clientY;
      touchMoved = false;
      updateMouseFromEvent(e);
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(planets);
      if (intersects.length > 0) {
        e.preventDefault();
        draggedPlanet = intersects[0].object as THREE.Mesh;
        setIsDragging(true);
      } else if (e.pointerType === "touch") {
        isScrollingPage = true;
        lastScrollTouchY = e.clientY;
      }
    }

    function onPointerUp(e: PointerEvent) {
      if (e.pointerType === "touch" && !touchMoved) {
        // A tap that didn't drag: on a planet/the sun, pin its fact card;
        // on empty space, unpin whatever was showing. This is the touch
        // equivalent of hover-in / hover-out, since touch has neither.
        updateMouseFromEvent(e);
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects([sun, ...planets]);
        if (intersects.length > 0) {
          const obj = intersects[0].object;
          const label = obj.userData.label as string;
          const fact = FACTS[label];
          if (fact) {
            hoveredMesh = obj;
            setHoveredFact(fact);
            setHoveredLabel(label);
            setCursorPos({ x: e.clientX, y: e.clientY });
          }
        } else {
          hoveredMesh = null;
          setHoveredFact(null);
        }
      }
      draggedPlanet = null;
      isScrollingPage = false;
      setIsDragging(false);
    }

    function onResize() {
      const aspect = window.innerWidth / window.innerHeight;
      const setup = cameraSetupForAspect(aspect);
      camera.aspect = aspect;
      camera.fov = setup.fov;
      camera.position.z = setup.distance;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("resize", onResize);

    let animationFrameId: number;
    function animate() {
      animationFrameId = requestAnimationFrame(animate);

      planets.forEach((p) => {
        if (p !== draggedPlanet) {
          p.userData.angle += 0.0018 * p.userData.speed;
        }
        p.position.x = Math.cos(p.userData.angle) * p.userData.dist;
        p.position.z = Math.sin(p.userData.angle) * p.userData.dist;
        p.rotation.y += p.userData.spin ?? 0.004;

        p.children.forEach((child) => {
          if (child.userData.isMoonlet) {
            child.userData.angle += 0.01 * child.userData.speed;
            child.position.x = Math.cos(child.userData.angle) * child.userData.dist;
            child.position.z = Math.sin(child.userData.angle) * child.userData.dist;
          }
        });
      });

      // Continuous hover-raycasting only makes sense for mouse/trackpad -
      // touch has no persistent pointer position between gestures, so this
      // would otherwise re-trigger against a stale last-touch coordinate.
      // Touch's equivalent (tap-to-pin) is handled entirely in onPointerUp.
      // Also skip entirely until a real pointer event has fired at least
      // once - see hasRealPointerPosition above.
      if (lastPointerWasTouch || !hasRealPointerPosition) {
        renderer.render(scene, camera);
        scene.rotation.y += draggedPlanet ? 0 : 0.0003;
        return;
      }

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects([sun, ...planets]);

      if (intersects.length > 0) {
        const obj = intersects[0].object;
        setIsPointerOverPlanet(true);
        if (hoveredMesh !== obj) {
          hoveredMesh = obj;
          const label = obj.userData.label as string;
          const fact = FACTS[label];
          if (fact) {
            setHoveredFact(fact);
            setHoveredLabel(label);
          }
        }
      } else {
        setIsPointerOverPlanet(false);
        if (hoveredMesh) {
          hoveredMesh = null;
          setHoveredFact(null);
        }
      }

      scene.rotation.y += draggedPlanet ? 0 : 0.0003;
      renderer.render(scene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry.dispose();
          const mat = obj.material;
          if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
          else mat.dispose();
        }
      });
    };
  }, []);

  return (
    <>
      <div
        ref={containerRef}
        className="fixed inset-0 z-0"
        style={{ cursor: isCoarsePointer ? "auto" : "none", touchAction: "none" }}
      />

      {/* Custom star cursor replaces the system cursor on mouse/trackpad
          only - there's no cursor to replace on a touchscreen. */}
      {!isCoarsePointer && (
        <div
          className="fixed z-40 pointer-events-none transition-transform duration-100"
          style={{
            left: cursorPos.x,
            top: cursorPos.y,
            transform: `translate(-50%, -50%) scale(${isDragging ? 1.4 : isPointerOverPlanet ? 1.2 : 1})`,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" style={{ filter: "drop-shadow(0 0 4px rgba(240,220,160,0.8))" }}>
            <path
              d="M9 0 L10.5 7.5 L18 9 L10.5 10.5 L9 18 L7.5 10.5 L0 9 L7.5 7.5 Z"
              fill={isDragging ? "#f0dca0" : "#ffffff"}
              opacity={isPointerOverPlanet || isDragging ? 1 : 0.85}
            />
          </svg>
        </div>
      )}

      <div className="fixed bottom-8 left-1/2 z-20 -translate-x-1/2 flex flex-col items-center gap-2 pointer-events-none">
        <span className="text-[11px] tracking-[0.2em] uppercase text-[#ede9f7]/70">Swipe down</span>
        <svg
          className="animate-bounce"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          style={{ opacity: 0.7 }}
        >
          <path d="M2 5 L8 11 L14 5" stroke="#ede9f7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      {hoveredFact && !isDragging && (
        <div
          className="glass fixed z-30 w-[280px] p-5 pointer-events-none transition-opacity"
          style={{
            left: Math.min(cursorPos.x + 24, (typeof window !== "undefined" ? window.innerWidth : 1200) - 300),
            top: Math.min(cursorPos.y - 20, (typeof window !== "undefined" ? window.innerHeight : 800) - 140),
            border: "1px solid rgba(201,168,106,0.35)",
          }}
        >
          <div className="text-[11px] tracking-wider uppercase text-goldLight mb-2 font-medium">
            {hoveredFact.name} · {hoveredLabel}
          </div>
          <div className="font-serif text-[17px] leading-snug text-[#ede9f7]">{hoveredFact.text}</div>
        </div>
      )}
    </>
  );
}
