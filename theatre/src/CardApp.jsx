import React from 'react';
import { Canvas } from '@react-three/fiber';
import CardDeck from './CardDeck';

function CardApp() {
  return (
    <Canvas
      camera={{ position: [0, 4, 10], fov: 45 }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 10, 5]} intensity={0.9} />
      <directionalLight position={[-5, 8, -5]} intensity={0.5} />
      <pointLight position={[0, 5, 5]} intensity={0.3} />
      <CardDeck />
    </Canvas>
  );
}

export default CardApp;

