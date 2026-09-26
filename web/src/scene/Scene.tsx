import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { texUrl, type Phase, type RodMotion, type ThermalMeta } from "../data";
import { depthToY, PAY_TOP_M } from "./geom";
import { HydraulicUnit, PumpJack, Wellhead } from "./PumpJack";
import { Ground, Reservoir, Steam, Well } from "./Well";

export interface StrokeClock { phase: number }

interface Props {
  thermal: ThermalMeta;
  frameIdx: number;
  phase: Phase;
  spm: number;
  unit: "beam" | "hydraulic";
  rod: RodMotion;
  floatStroke: boolean;
  fluidZ: number[];
  fluidT: number[];
  TinC: number;
  present: boolean;
  frozenPhase: number | null;
  onReady?: () => void;
}

function ClockDriver({ clock, spm, frozen }: { clock: React.MutableRefObject<StrokeClock>; spm: number; frozen: number | null }) {
  useFrame((_, dt) => {
    if (frozen !== null) {
      clock.current.phase = frozen;
      return;
    }
    if (spm > 0) clock.current.phase = (clock.current.phase + (Math.min(dt, 0.1) * spm) / 60) % 1;
  });
  return null;
}

function useTextures(meta: ThermalMeta, onLoaded: () => void) {
  const [tex, setTex] = useState<THREE.Texture[]>([]);
  useEffect(() => {
    const mgr = new THREE.LoadingManager(onLoaded);
    const loader = new THREE.TextureLoader(mgr);
    const t = meta.frames.map((f) => {
      const x = loader.load(texUrl(f.tex));
      x.colorSpace = THREE.SRGBColorSpace;
      x.wrapS = x.wrapT = THREE.ClampToEdgeWrapping;
      x.generateMipmaps = false;
      x.minFilter = THREE.LinearFilter;
      return x;
    });
    setTex(t);
    return () => t.forEach((x) => x.dispose());
  }, [meta]); // eslint-disable-line react-hooks/exhaustive-deps
  return tex;
}

function FrameCounter({ onReady, texReady }: { onReady?: () => void; texReady: boolean }) {
  const n = useRef(0);
  const fired = useRef(false);
  useFrame(() => {
    if (!texReady || fired.current) return;
    if (++n.current > 20) {
      fired.current = true;
      onReady?.();
    }
  });
  return null;
}

export default function Scene(p: Props) {
  const clock = useRef<StrokeClock>({ phase: 0.3 });
  const [texReady, setTexReady] = useState(false);
  const textures = useTextures(p.thermal, () => setTexReady(true));
  const tex = textures[p.frameIdx] ?? null;
  const stroke = p.floatStroke ? p.rod.float : p.rod;
  const glow = useMemo(() => new THREE.Color().setHSL(0.07, 0.9, 0.55), []);
  const moving = p.phase === "production" && p.spm > 0;

  return (
    <Canvas
      dpr={p.present ? 2 : [1, 2]}
      gl={{ antialias: true, preserveDrawingBuffer: true }}
      camera={{ position: [46, 5, 58], fov: 30, near: 0.5, far: 400 }}
      onCreated={({ gl }) => gl.setClearColor("#0b0f0d")}
    >
      <ClockDriver clock={clock} spm={moving ? p.spm : 0} frozen={p.frozenPhase} />
      <FrameCounter onReady={p.onReady} texReady={texReady} />
      <ambientLight intensity={0.45} />
      <hemisphereLight args={["#cfe0ff", "#1a1410", 0.5]} />
      <directionalLight position={[12, 22, 16]} intensity={1.6} />
      <pointLight
        position={[3, depthToY(PAY_TOP_M + 2), 3]}
        color={glow}
        intensity={Math.max(0, (p.TinC - 60) / 250) * 60}
        distance={18}
      />
      <group position={[0, 0, 0]}>
        {p.unit === "beam" ? <PumpJack clock={clock} /> : <HydraulicUnit clock={clock} />}
        <Wellhead />
        <Ground />
        <Well
          clock={clock}
          depth_m={p.rod.depth_m}
          stroke={stroke}
          moving={moving}
          fluidZ={p.fluidZ}
          fluidT={p.fluidT}
          labels
        />
        <Reservoir tex={tex} labels />
        <Steam on={p.phase === "injection"} />
      </group>
      <OrbitControls target={[0, -10.5, 0]} enableDamping makeDefault maxDistance={120} minDistance={8} />
      <EffectComposer multisampling={4}>
        <Bloom mipmapBlur intensity={0.85} luminanceThreshold={0.95} luminanceSmoothing={0.2} />
        <Vignette offset={0.25} darkness={0.55} />
      </EffectComposer>
    </Canvas>
  );
}
