import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  return reduced;
}

function DemandClock({ active }) {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    invalidate();
    if (!active) return undefined;
    const timer = window.setInterval(invalidate, 1000 / 20);
    return () => window.clearInterval(timer);
  }, [active, invalidate]);

  return null;
}

function StarField() {
  const positions = useMemo(() => {
    const values = new Float32Array(120 * 3);
    for (let index = 0; index < 120; index += 1) {
      const phase = index * 2.399963;
      const radius = 4.8 + (index % 12) * 0.32;
      values[index * 3] = Math.cos(phase) * radius;
      values[index * 3 + 1] = ((index * 37) % 83) / 9 - 4.5;
      values[index * 3 + 2] = Math.sin(phase) * radius - 2.2;
    }
    return values;
  }, []);

  return (
    <points>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry>
      <pointsMaterial color="#c8fff0" size={0.032} transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}

function TransitRays() {
  const positions = useMemo(() => {
    const values = new Float32Array(8 * 6);
    for (let index = 0; index < 8; index += 1) {
      const y = -1.4 + index * 0.4;
      values[index * 6] = -4.2;
      values[index * 6 + 1] = y;
      values[index * 6 + 2] = -1.2;
      values[index * 6 + 3] = 2.5;
      values[index * 6 + 4] = y * 0.55;
      values[index * 6 + 5] = -1.2;
    }
    return values;
  }, []);

  return (
    <lineSegments>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry>
      <lineBasicMaterial color="#8affdb" transparent opacity={0.16} />
    </lineSegments>
  );
}

function TransitModel({ animate }) {
  const planet = useRef(null);
  const system = useRef(null);

  useFrame(({ clock }) => {
    if (!animate) return;
    const elapsed = clock.getElapsedTime();
    if (planet.current) planet.current.rotation.y = elapsed * 0.1;
    if (system.current) {
      system.current.rotation.z = Math.sin(elapsed * 0.22) * 0.035 - 0.1;
      system.current.position.y = Math.sin(elapsed * 0.45) * 0.06;
    }
  });

  return (
    <group ref={system}>
      <mesh position={[-3.55, 0.25, -2.6]}>
        <sphereGeometry args={[1.8, 32, 24]} />
        <meshStandardMaterial color="#c2fff1" emissive="#6eeccf" emissiveIntensity={1.9} roughness={0.9} />
      </mesh>
      <TransitRays />
      <group ref={planet} position={[0.4, 0, 0]} rotation={[0.08, 0.15, -0.12]}>
        <mesh>
          <icosahedronGeometry args={[1.28, 5]} />
          <meshStandardMaterial color="#062a2a" roughness={0.82} metalness={0.05} />
        </mesh>
        <mesh>
          <sphereGeometry args={[1.39, 48, 24]} />
          <meshBasicMaterial color="#5ff4cf" transparent opacity={0.1} side={2} depthWrite={false} />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0.15, 0]}>
          <torusGeometry args={[1.43, 0.025, 8, 80]} />
          <meshBasicMaterial color="#83ffe0" transparent opacity={0.82} />
        </mesh>
        <mesh rotation={[Math.PI / 2.3, -0.25, 0.3]}>
          <torusGeometry args={[1.53, 0.014, 8, 80]} />
          <meshBasicMaterial color="#4be6f0" transparent opacity={0.42} />
        </mesh>
      </group>
      <mesh rotation={[Math.PI / 2.25, 0.1, 0.22]}>
        <torusGeometry args={[2.9, 0.012, 8, 120]} />
        <meshBasicMaterial color="#59cdbd" transparent opacity={0.28} />
      </mesh>
      <mesh position={[2.85, -0.55, 0]}>
        <sphereGeometry args={[0.09, 12, 8]} />
        <meshBasicMaterial color="#b7fff0" />
      </mesh>
    </group>
  );
}

export default function AtmosphereHero() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="atmosphere-canvas" role="img" aria-label="Procedural exoplanet transit and atmospheric limb schematic">
      <Canvas camera={{ position: [4.8, 2.7, 6.5], fov: 38 }} dpr={[1, 1.35]} frameloop="demand" gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }}>
        <ambientLight intensity={0.55} />
        <pointLight position={[-3.5, 1, 3]} intensity={32} color="#b6ffe9" />
        <pointLight position={[3, -1, 2]} intensity={12} color="#48dbea" />
        <StarField />
        <TransitModel animate={!reducedMotion} />
        <DemandClock active={!reducedMotion} />
      </Canvas>
    </div>
  );
}
