import { Html, Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { COLORS, inferno, type RodStroke } from "../data";
import {
  depthToY, MID_END_M, PAY_H, PAY_TOP_M, PUMP_DEPTH_M, R_CASING, R_RES, R_ROD, R_TUB_I, R_TUB_O, scaleAt, TOP_M,
  WIN_BOT_M, WIN_TOP_M,
} from "./geom";
import type { StrokeClock } from "./Scene";

// depth samples for the rod / fluid segments: dense where the depth is to scale
const DEPTHS = (() => {
  const d: number[] = [];
  for (let x = 0; x < TOP_M; x += 1) d.push(x);
  for (let x = TOP_M; x < MID_END_M; x += 10) d.push(x);
  for (let x = MID_END_M; x <= PUMP_DEPTH_M; x += 1) d.push(x);
  return d;
})();
const NSEG = DEPTHS.length - 1;

const interp = (xs: number[], ys: number[], x: number) => {
  if (x <= xs[0]) return ys[0];
  for (let k = 1; k < xs.length; k++) {
    if (x <= xs[k]) return ys[k - 1] + ((ys[k] - ys[k - 1]) * (x - xs[k - 1])) / (xs[k] - xs[k - 1]);
  }
  return ys[ys.length - 1];
};

// rod stress colour: tension blue-grey -> sand -> orange; compression (float) bright red
const C_LO = new THREE.Color("#2f5d8c"), C_MID = new THREE.Color("#d8d2c4"), C_HI = new THREE.Color("#e8742f");
const C_NEG = new THREE.Color("#ff3b3b");
export const STRESS_RANGE: [number, number] = [0, 130];
function stressColor(s: number, out: THREE.Color) {
  if (s < 0) return out.copy(C_NEG);
  const t = Math.min(1, s / STRESS_RANGE[1]);
  return t < 0.5 ? out.copy(C_LO).lerp(C_MID, t * 2) : out.copy(C_MID).lerp(C_HI, (t - 0.5) * 2);
}

interface Props {
  clock: React.MutableRefObject<StrokeClock>;
  depth_m: number[];
  stroke: RodStroke;
  moving: boolean;
  fluidZ: number[];
  fluidT: number[];
  labels: boolean;
}

const tmp = new THREE.Object3D();
const col = new THREE.Color();

export function Well({ clock, depth_m, stroke, moving, fluidZ, fluidT, labels }: Props) {
  const rod = useRef<THREE.InstancedMesh>(null!);
  const fluid = useRef<THREE.InstancedMesh>(null!);
  const ubar = useMemo(
    () => depth_m.map((_, j) => stroke.u_m.reduce((a, r) => a + r[j], 0) / stroke.u_m.length),
    [depth_m, stroke],
  );

  // fluid column coloured by tubing temperature (inferno, 50-310 C as the reservoir)
  useEffect(() => {
    for (let i = 0; i < NSEG; i++) {
      const d0 = DEPTHS[i], d1 = DEPTHS[i + 1];
      const y0 = depthToY(d0), y1 = depthToY(d1);
      tmp.position.set(0, (y0 + y1) / 2, 0);
      tmp.scale.set(1, Math.abs(y1 - y0), 1);
      tmp.quaternion.identity();
      tmp.updateMatrix();
      fluid.current.setMatrixAt(i, tmp.matrix);
      const T = interp(fluidZ, fluidT, (d0 + d1) / 2);
      fluid.current.setColorAt(i, col.set(inferno((T - 50) / 260)));
    }
    fluid.current.instanceMatrix.needsUpdate = true;
    if (fluid.current.instanceColor) fluid.current.instanceColor.needsUpdate = true;
  }, [fluidZ, fluidT]);

  useFrame(() => {
    const k = Math.min(stroke.u_m.length - 1, Math.floor(clock.current.phase * stroke.u_m.length));
    const u = stroke.u_m[k], s = stroke.stress_MPa[k];
    for (let i = 0; i < NSEG; i++) {
      const d0 = DEPTHS[i], d1 = DEPTHS[i + 1];
      const off = (d: number) => (moving ? -(interp(depth_m, u, d) - interp(depth_m, ubar, d)) * scaleAt(d) : 0);
      const y0 = depthToY(d0) + off(d0), y1 = depthToY(d1) + off(d1);
      tmp.position.set(0, (y0 + y1) / 2, 0);
      tmp.scale.set(1, Math.max(1e-3, Math.abs(y1 - y0)), 1);
      tmp.quaternion.identity();
      tmp.updateMatrix();
      rod.current.setMatrixAt(i, tmp.matrix);
      rod.current.setColorAt(i, stressColor(moving ? interp(depth_m, s, (d0 + d1) / 2) : 20, col));
    }
    rod.current.instanceMatrix.needsUpdate = true;
    if (rod.current.instanceColor) rod.current.instanceColor.needsUpdate = true;
  });

  const yPayBot = depthToY(PAY_TOP_M + PAY_H.reduce((a, b) => a + b, 0));
  const casingH = -yPayBot;
  const tubH = -depthToY(PUMP_DEPTH_M);
  const zig = (y: number) =>
    Array.from({ length: 9 }, (_, k) => [-0.9 + (k * 1.8) / 8, y + (k % 2 ? 0.14 : -0.14), 0.6] as [number, number, number]);

  return (
    <group>
      {/* casing, cut away toward the camera like the reservoir */}
      <mesh position={[0, -casingH / 2, 0]}>
        <cylinderGeometry args={[R_CASING, R_CASING, casingH, 40, 1, true, Math.PI / 2, 1.5 * Math.PI]} />
        <meshStandardMaterial color="#8d9892" metalness={0.7} roughness={0.35} side={THREE.DoubleSide} />
      </mesh>
      {/* VIT tubing: outer wall translucent, vacuum gap, inner wall */}
      <mesh position={[0, -tubH / 2 + 0.6, 0]}>
        <cylinderGeometry args={[R_TUB_O, R_TUB_O, tubH + 1.2, 32, 1, true]} />
        <meshStandardMaterial color={COLORS.wellboreL} transparent opacity={0.22} metalness={0.3} roughness={0.3} depthWrite={false} />
      </mesh>
      <instancedMesh ref={fluid} args={[undefined, undefined, NSEG]}>
        <cylinderGeometry args={[R_TUB_I, R_TUB_I, 1, 20, 1, true]} />
        <meshBasicMaterial transparent opacity={0.5} depthWrite={false} toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={rod} args={[undefined, undefined, NSEG]}>
        <cylinderGeometry args={[R_ROD, R_ROD, 1, 10]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      {/* pump barrel */}
      <mesh position={[0, depthToY(PUMP_DEPTH_M + 1.5), 0]}>
        <cylinderGeometry args={[R_TUB_O * 1.25, R_TUB_O * 1.25, 1.6, 24]} />
        <meshStandardMaterial color="#b9c2bd" metalness={0.8} roughness={0.3} />
      </mesh>
      {/* break symbols around the compressed section */}
      <Line points={zig(depthToY(TOP_M) - 0.15)} color="#4A534E" lineWidth={1.6} />
      <Line points={zig(depthToY(MID_END_M) + 0.15)} color="#4A534E" lineWidth={1.6} />
      {labels && (
        <>
          <Html position={[1.0, depthToY(12), 0]} className="lbl">Insulated tubing · colour = fluid temperature</Html>
          <Html position={[1.0, depthToY(24), 0]} className="lbl">Sucker rods · colour = stress</Html>
          <Html position={[1.2, depthToY(560), 0]} className="lbl dim">
            30 m to 1,090 m depth shortened
          </Html>
          <Html position={[0.9, depthToY(PUMP_DEPTH_M + 1.5), 0]} className="lbl">Pump at 1,100 m</Html>
        </>
      )}
    </group>
  );
}

// ------------------------------------------------------------------ reservoir
const VERT = /* glsl */ `
varying vec3 vPos;
void main() {
  vec4 w = modelMatrix * vec4(position, 1.0);
  vPos = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;
const FRAG = /* glsl */ `
uniform sampler2D tex;
uniform float R;
uniform float yTop;
uniform float yBot;
uniform float glow;
varying vec3 vPos;
void main() {
  float u = clamp(length(vPos.xz) / R, 0.002, 0.998);
  float v = clamp((yTop - vPos.y) / (yTop - yBot), 0.002, 0.998);
  vec3 c = texture2D(tex, vec2(u, 1.0 - v)).rgb;
  float l = dot(c, vec3(0.299, 0.587, 0.114));
  c = c * (1.0 + glow * smoothstep(0.25, 0.8, l)) + vec3(0.03, 0.028, 0.026);
  gl_FragColor = vec4(c, 1.0);
  #include <colorspace_fragment>
}`;

export function Reservoir({ tex, labels }: { tex: THREE.Texture | null; labels: boolean }) {
  const yTop = depthToY(WIN_TOP_M), yBot = depthToY(WIN_BOT_M);
  const H = yTop - yBot, yc = (yTop + yBot) / 2;
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: FRAG,
        uniforms: { tex: { value: null }, R: { value: R_RES }, yTop: { value: yTop }, yBot: { value: yBot }, glow: { value: 2.2 } },
        side: THREE.DoubleSide,
        toneMapped: false,
      }),
    [yTop, yBot],
  );
  useEffect(() => {
    mat.uniforms.tex.value = tex;
  }, [tex, mat]);

  const tops = [0, 4, 7, 10].map((h) => depthToY(PAY_TOP_M + h));
  const faceLine = (y: number, dashed: boolean, k: number) => (
    <group key={k}>
      <Line points={[[0, y, 0.001], [R_RES, y, 0.001]]} color="#e8ece9" lineWidth={1} transparent opacity={dashed ? 0.35 : 0.6} dashed={dashed} dashSize={0.3} gapSize={0.2} />
      <Line points={[[0.001, y, 0], [0.001, y, R_RES]]} color="#e8ece9" lineWidth={1} transparent opacity={dashed ? 0.35 : 0.6} dashed={dashed} dashSize={0.3} gapSize={0.2} />
    </group>
  );
  return (
    <group>
      <mesh position={[0, yc, 0]} material={mat}>
        <cylinderGeometry args={[R_RES, R_RES, H, 96, 1, false, Math.PI / 2, 1.5 * Math.PI]} />
      </mesh>
      <mesh position={[R_RES / 2, yc, 0]} material={mat}>
        <planeGeometry args={[R_RES, H]} />
      </mesh>
      <mesh position={[0, yc, R_RES / 2]} rotation={[0, Math.PI / 2, 0]} material={mat}>
        <planeGeometry args={[R_RES, H]} />
      </mesh>
      {tops.map((y, k) => faceLine(y, k === 1 || k === 2, k))}
      {labels && (
        <>
          <Html position={[R_RES - 2.6, (tops[0] + tops[3]) / 2, 0.05]} center className="lbl tiny">3 oil layers</Html>
          <Html position={[R_RES + 0.6, tops[0] + 0.1, 0]} className="lbl">Oil sand at ≈ 1,150 m</Html>
          <Html position={[R_RES - 1.2, yTop - 0.9, 0.05]} center className="lbl tiny dim">cap rock</Html>
          <Html position={[2.2, yBot + 0.9, 0.05]} center className="lbl tiny dim">base rock</Html>
          <Html position={[R_RES * 0.55, yBot - 1.1, 0.05]} center className="lbl tiny dim">Distance from the well: 0.1 m at the centre to 150 m at the edge (log scale)</Html>
        </>
      )}
    </group>
  );
}

export function Ground() {
  const yRes = depthToY(WIN_TOP_M);
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <ringGeometry args={[R_CASING + 0.02, R_RES, 96, 1, 0, 1.5 * Math.PI]} />
        <meshStandardMaterial color="#D5DBD3" roughness={1} side={THREE.DoubleSide} />
      </mesh>
      {/* earth cut faces between the surface and the reservoir window */}
      <mesh position={[(R_RES + R_CASING) / 2, yRes / 2, -0.01]}>
        <planeGeometry args={[R_RES - R_CASING, -yRes]} />
        <meshBasicMaterial color="#C9C1B1" transparent opacity={0.45} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <mesh position={[-0.01, yRes / 2, (R_RES + R_CASING) / 2]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[R_RES - R_CASING, -yRes]} />
        <meshBasicMaterial color="#BDB4A3" transparent opacity={0.45} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
    </group>
  );
}

export function Steam({ on }: { on: boolean }) {
  const N = 260;
  const ref = useRef<THREE.Points>(null!);
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const p = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      const a = Math.random() * Math.PI * 2, r = Math.random() * R_TUB_I * 0.8;
      p[3 * i] = r * Math.cos(a);
      p[3 * i + 1] = -Math.random() * -depthToY(PUMP_DEPTH_M + 30);
      p[3 * i + 2] = r * Math.sin(a);
    }
    g.setAttribute("position", new THREE.BufferAttribute(p, 3));
    return g;
  }, []);
  useFrame((_, dt) => {
    if (!on) return;
    const p = geo.attributes.position as THREE.BufferAttribute;
    const yEnd = depthToY(PAY_TOP_M + 5);
    for (let i = 0; i < N; i++) {
      let y = p.getY(i) - dt * 3.0;
      if (y < yEnd) y = 0.5;
      p.setY(i, y);
    }
    p.needsUpdate = true;
  });
  return (
    <points ref={ref} geometry={geo} visible={on}>
      <pointsMaterial size={0.12} color="#fff1dc" transparent opacity={0.85} blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false} />
    </points>
  );
}
