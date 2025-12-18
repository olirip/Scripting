import React from 'react';
import { Canvas } from '@react-three/fiber';
import Scene from './Scene';

function App() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 75 }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <Scene />
    </Canvas>
  );
}

export default App;


