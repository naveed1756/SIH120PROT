import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { COLORS } from "../data";
import { beamY, hydY, STROKE } from "./geom";
import type { StrokeClock } from "./Scene";

// Conventional beam unit, true scale (m). Horsehead arc of radius A centred on the saddle
// bearing keeps the bridle tangent point fixed at (0, PIVOT_Y), so the carrier bar moves by
// the arc length A*phi: phi = (y - S/2) / A.
const A = 3.0;
const C = 2.0;
const PIVOT = new THREE.Vector3(-A, 5.0, 0);
const CRANK = new THREE.Vector3(-A - C, 1.55, 0);
const RC = 1.0;
const WELLHEAD_TOP = 1.15;
const CARRIER_MID = 3.1;

const steel = new THREE.MeshStandardMaterial({ color: "#59625d", metalness: 0.6, roughness: 0.45 });
const body = new THREE.MeshStandardMaterial({ color: COLORS.surface, metalness: 0.35, roughness: 0.55 });
const dark = new THREE.MeshStandardMaterial({ color: "#2a302d", metalness: 0.5, roughness: 0.6 });
const rodMat = new THREE.MeshStandardMaterial({ color: "#c9d1cc", metalness: 0.9, roughness: 0.25 });

function between(m: THREE.Object3D, a: THREE.Vector3, b: THREE.Vector3) {
  const d = new THREE.Vector3().subVectors(b, a);
  m.position.copy(a).addScaledVector(d, 0.5);
  m.scale.set(1, d.length(), 1);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
}

export function Wellhead() {
  return (
    <group>
      <mesh position={[0, 0.25, 0]} material={steel}>
        <cylinderGeometry args={[0.36, 0.4, 0.5, 24]} />
      </mesh>
      <mesh position={[0, 0.7, 0]} material={steel}>
        <cylinderGeometry args={[0.24, 0.24, 0.4, 24]} />
      </mesh>
      <mesh position={[0.45, 0.65, 0]} rotation={[0, 0, Math.PI / 2]} material={steel}>
        <cylinderGeometry args={[0.1, 0.1, 0.6, 12]} />
      </mesh>
      <mesh position={[0, WELLHEAD_TOP - 0.1, 0]} material={dark}>
        <cylinderGeometry args={[0.16, 0.2, 0.2, 16]} />
      </mesh>
    </group>
  );
}

function PolishedRod({ yRef }: { yRef: React.MutableRefObject<number> }) {
  const rod = useRef<THREE.Mesh>(null!);
  const bar = useRef<THREE.Group>(null!);
  useFrame(() => {
    const yc = CARRIER_MID + (yRef.current - STROKE / 2);
    between(rod.current, new THREE.Vector3(0, WELLHEAD_TOP - 0.2, 0), new THREE.Vector3(0, yc + 0.35, 0));
    bar.current.position.y = yc;
  });
  return (
    <>
      <mesh ref={rod} material={rodMat}>
        <cylinderGeometry args={[0.035, 0.035, 1, 10]} />
      </mesh>
      <group ref={bar}>
        <mesh material={dark}>
          <boxGeometry args={[0.7, 0.12, 0.22]} />
        </mesh>
        <mesh position={[0, 0.2, 0]} material={steel}>
          <boxGeometry args={[0.16, 0.2, 0.16]} />
        </mesh>
      </group>
    </>
  );
}

export function PumpJack({ clock }: { clock: React.MutableRefObject<StrokeClock> }) {
  const beam = useRef<THREE.Group>(null!);
  const crank = useRef<THREE.Group>(null!);
  const pitL = useRef<THREE.Mesh>(null!);
  const pitR = useRef<THREE.Mesh>(null!);
  const bridle = useRef<THREE.Mesh>(null!);
  const yRef = useRef(0);

  const horsehead = useMemo(() => {
    const s = new THREE.Shape();
    const a0 = -0.62, a1 = 0.62, rOut = A, rIn = A - 1.05;
    s.moveTo(rIn * Math.cos(a0), rIn * Math.sin(a0));
    s.absarc(0, 0, rOut, a0, a1, false);
    s.lineTo(rIn * Math.cos(a1), rIn * Math.sin(a1));
    s.lineTo(rIn * Math.cos(a0), rIn * Math.sin(a0));
    const g = new THREE.ExtrudeGeometry(s, { depth: 0.46, bevelEnabled: false, curveSegments: 32 });
    g.translate(0, 0, -0.23);
    return g;
  }, []);

  useFrame(() => {
    const y = beamY(clock.current.phase);
    yRef.current = y;
    const phi = (y - STROKE / 2) / A;
    beam.current.rotation.z = phi;
    const th = Math.PI / 2 + 2 * Math.PI * clock.current.phase;
    crank.current.rotation.z = th - Math.PI / 2;
    const rear = new THREE.Vector3(PIVOT.x - C * Math.cos(phi), PIVOT.y - C * Math.sin(phi), 0);
    for (const [m, z] of [[pitL.current, 0.55], [pitR.current, -0.55]] as const) {
      const pin = new THREE.Vector3(CRANK.x + RC * Math.cos(th), CRANK.y + RC * Math.sin(th), z);
      between(m, pin, new THREE.Vector3(rear.x, rear.y, z * 0.5));
    }
    const yc = CARRIER_MID + (y - STROKE / 2);
    between(bridle.current, new THREE.Vector3(0.02, yc + 0.08, 0), new THREE.Vector3(0.02, PIVOT.y, 0));
  });

  return (
    <group>
      {/* base skid */}
      <mesh position={[-3.6, 0.15, 0]} material={dark}>
        <boxGeometry args={[6.6, 0.3, 1.5]} />
      </mesh>
      {/* samson post (A-frame) */}
      {[
        [0.55, -0.55],
        [-0.55, 0.55],
      ].map(([z0], k) => (
        <mesh key={k} material={body} position={[PIVOT.x - 0.55, PIVOT.y / 2, z0 * 1.0]} rotation={[z0 > 0 ? 0.12 : -0.12, 0, -0.12]}>
          <boxGeometry args={[0.2, PIVOT.y, 0.2]} />
        </mesh>
      ))}
      <mesh material={body} position={[PIVOT.x + 0.45, PIVOT.y / 2 - 0.1, 0]} rotation={[0, 0, 0.2]}>
        <boxGeometry args={[0.18, PIVOT.y, 0.18]} />
      </mesh>
      {/* walking beam + horsehead */}
      <group ref={beam} position={PIVOT.toArray()}>
        <mesh material={body} position={[(A - 1.0 - C) / 2, 0.05, 0]}>
          <boxGeometry args={[A - 1.0 + C + 0.4, 0.42, 0.34]} />
        </mesh>
        <mesh geometry={horsehead} material={body} />
        <mesh material={dark} position={[-C, -0.2, 0]}>
          <boxGeometry args={[0.3, 0.3, 1.2]} />
        </mesh>
        <mesh material={steel} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.16, 0.16, 0.6, 16]} />
        </mesh>
      </group>
      {/* gear reducer, crank arms + counterweights, motor */}
      <mesh position={[CRANK.x, 0.95, 0]} material={body}>
        <boxGeometry args={[1.3, 1.3, 0.9]} />
      </mesh>
      <group ref={crank} position={CRANK.toArray()}>
        {[0.55, -0.55].map((z) => (
          <group key={z} position={[0, 0, z]}>
            <mesh material={dark} position={[0, RC / 2 - 0.35, 0]}>
              <boxGeometry args={[0.28, RC + 0.7, 0.12]} />
            </mesh>
            <mesh material={steel} position={[0, -0.75, 0]}>
              <boxGeometry args={[1.25, 0.75, 0.2]} />
            </mesh>
          </group>
        ))}
      </group>
      <mesh ref={pitL} material={steel}>
        <cylinderGeometry args={[0.05, 0.05, 1, 8]} />
      </mesh>
      <mesh ref={pitR} material={steel}>
        <cylinderGeometry args={[0.05, 0.05, 1, 8]} />
      </mesh>
      <mesh position={[CRANK.x - 1.4, 0.65, 0]} material={steel}>
        <cylinderGeometry args={[0.35, 0.35, 0.8, 16]} />
      </mesh>
      <mesh ref={bridle} material={rodMat}>
        <cylinderGeometry args={[0.018, 0.018, 1, 6]} />
      </mesh>
      <PolishedRod yRef={yRef} />
    </group>
  );
}

export function HydraulicUnit({ clock }: { clock: React.MutableRefObject<StrokeClock> }) {
  const yRef = useRef(0);
  const piston = useRef<THREE.Mesh>(null!);
  useFrame(() => {
    const y = hydY(clock.current.phase);
    yRef.current = y;
    const yc = CARRIER_MID + (y - STROKE / 2);
    between(piston.current, new THREE.Vector3(0, yc + 0.3, 0), new THREE.Vector3(0, 6.2, 0));
  });
  return (
    <group>
      <mesh position={[0, 7.3, 0]} material={body}>
        <cylinderGeometry args={[0.28, 0.28, 3.0, 24]} />
      </mesh>
      {[0.7, -0.7].map((x) => (
        <mesh key={x} position={[x, 4.4, 0]} material={body}>
          <boxGeometry args={[0.14, 8.8, 0.14]} />
        </mesh>
      ))}
      <mesh position={[0, 8.85, 0]} material={body}>
        <boxGeometry args={[1.6, 0.16, 0.5]} />
      </mesh>
      <mesh ref={piston} material={rodMat}>
        <cylinderGeometry args={[0.07, 0.07, 1, 12]} />
      </mesh>
      <mesh position={[-3.2, 0.6, 0.6]} material={body}>
        <boxGeometry args={[1.8, 1.2, 1.2]} />
      </mesh>
      <PolishedRod yRef={yRef} />
    </group>
  );
}
