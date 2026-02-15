/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial, Sphere, Torus, Cylinder, Stars, Environment, Box } from '@react-three/drei';
import * as THREE from 'three';

const QuantumParticle = ({ position, color, scale = 1 }: { position: [number, number, number]; color: string; scale?: number }) => {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.getElapsedTime();
      ref.current.position.y = position[1] + Math.sin(t * 2 + position[0]) * 0.2;
      ref.current.rotation.x = t * 0.5;
      ref.current.rotation.z = t * 0.3;
    }
  });

  return (
    <Sphere ref={ref} args={[1, 32, 32]} position={position} scale={scale}>
      <MeshDistortMaterial
        color={color}
        envMapIntensity={1}
        clearcoat={1}
        clearcoatRoughness={0}
        metalness={0.5}
        distort={0.4}
        speed={2}
      />
    </Sphere>
  );
};

const MacroscopicWave = () => {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
       const t = state.clock.getElapsedTime();
       ref.current.rotation.x = Math.sin(t * 0.2) * 0.2;
       ref.current.rotation.y = t * 0.1;
    }
  });

  return (
    <Torus ref={ref} args={[3, 0.1, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
      <meshStandardMaterial color="#C5A059" emissive="#C5A059" emissiveIntensity={0.5} transparent opacity={0.6} wireframe />
    </Torus>
  );
}

export const HeroScene: React.FC = () => {
  return (
    <div className="absolute inset-0 z-0 opacity-60 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
          <QuantumParticle position={[0, 0, 0]} color="#4F46E5" scale={1.2} />
          <MacroscopicWave />
        </Float>
        
        <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
           <QuantumParticle position={[-3, 1, -2]} color="#9333EA" scale={0.5} />
           <QuantumParticle position={[3, -1, -3]} color="#C5A059" scale={0.6} />
        </Float>

        <Environment preset="city" />
        <Stars radius={100} depth={50} count={1000} factor={4} saturation={0} fade speed={1} />
      </Canvas>
    </div>
  );
};

export const QuantumComputerScene: React.FC = () => {
  return (
    <div className="w-full h-full absolute inset-0">
      <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }}>
        <ambientLight intensity={1} />
        <spotLight position={[5, 5, 5]} angle={0.3} penumbra={1} intensity={2} color="#C5A059" />
        <pointLight position={[-5, -5, -5]} intensity={0.5} />
        <Environment preset="studio" />
        
        <Float rotationIntensity={0.4} floatIntensity={0.2} speed={1}>
          <group rotation={[0, 0, 0]} position={[0, 0.5, 0]}>
            {/* Main Cryostat Structure (Gold Chandelier) */}
            
            {/* Top Plate */}
            <Cylinder args={[1.2, 1.2, 0.1, 64]} position={[0, 1, 0]}>
              <meshStandardMaterial color="#C5A059" metalness={1} roughness={0.15} />
            </Cylinder>
            
            {/* Middle Stage */}
            <Cylinder args={[1, 1, 0.1, 64]} position={[0, 0.2, 0]}>
              <meshStandardMaterial color="#C5A059" metalness={1} roughness={0.15} />
            </Cylinder>
            
            {/* Bottom Stage (Mixing Chamber) */}
            <Cylinder args={[0.6, 0.6, 0.1, 64]} position={[0, -0.6, 0]}>
              <meshStandardMaterial color="#C5A059" metalness={1} roughness={0.15} />
            </Cylinder>

            {/* Connecting Rods */}
            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0.5, 0.6, 0]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[-0.5, 0.6, 0]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
             <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0, 0.6, 0.5]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
             <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0, 0.6, -0.5]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>

             {/* Lower Rods */}
             <Cylinder args={[0.03, 0.03, 0.8, 16]} position={[0.2, -0.2, 0]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.03, 0.03, 0.8, 16]} position={[-0.2, -0.2, 0]}>
               <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Coils/Wires - Copper colored */}
            <Torus args={[0.7, 0.015, 16, 64]} position={[0, -0.2, 0]} rotation={[Math.PI/2, 0, 0]}>
               <meshStandardMaterial color="#B87333" metalness={0.8} roughness={0.3} />
            </Torus>
             <Torus args={[0.3, 0.015, 16, 64]} position={[0, -1, 0]} rotation={[Math.PI/2, 0, 0]}>
               <meshStandardMaterial color="#B87333" metalness={0.8} roughness={0.3} />
            </Torus>
            
            {/* Central processor chip simulation at bottom */}
            <Box args={[0.2, 0.05, 0.2]} position={[0, -0.7, 0]}>
                <meshStandardMaterial color="#111" metalness={0.9} roughness={0.1} />
            </Box>
          </group>
        </Float>
      </Canvas>
    </div>
  );
}