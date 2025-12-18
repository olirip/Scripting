import React, { useRef, useEffect } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { Vector3, TextureLoader } from 'three';

// Individual cube face component
function CubeFace({ basePosition, rotation, normal, scrollProgressRef, splitThreshold, texture }) {
  const meshRef = useRef(null);
  const posRef = useRef(new Vector3(...basePosition));
  
  useFrame(() => {
    if (meshRef.current) {
      const scrollProgress = scrollProgressRef.current;
      // Split starts after splitThreshold (2 page heights)
      // Split amount increases linearly after that point
      const splitAmount = Math.max(0, scrollProgress - splitThreshold);
      const offset = new Vector3(...normal).multiplyScalar(splitAmount * 2);
      meshRef.current.position.copy(posRef.current).add(offset);
    }
  });

  return (
    <mesh ref={meshRef} position={basePosition} rotation={rotation}>
      <planeGeometry args={[2, 2]} />
      <meshStandardMaterial map={texture} side={2} />
    </mesh>
  );
}

function Cube() {
  const groupRef = useRef(null);
  const scrollProgressRef = useRef(0);
  const splitThreshold = 2; // 2 page heights

  // Load all 6 images as textures
  const textures = useLoader(TextureLoader, [
    '/asset/rolex-testimonee-arts-cinema-zendaya-landscape-thumbnail_zendaya_b_092125_alt_non_blur_iso_08_2.jpg',
    '/asset/rolex-testimonee-camille-rast-landscape-thumbnail-gettyimages-2191912350.jpg',
    '/asset/rolex-testimonee-mira-andreeva-tennis-square-gettyimages-1494518744.jpg',
    '/asset/rolex-testimonee-planet-kris-tompkins-landscape-thumbnail_tc_pnpc_marcelomascareno.jpg',
    '/asset/rolex-testimonee-renaud-capucon-square-thumbnail-image015.jpg',
    '/asset/rolex-testimonies-equestrianism-sophie-hinners-grid-square-thumbnail_smm_2509an_3368.jpg',
  ]);

  // Listen to scroll events
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
      const pageHeight = window.innerHeight;
      scrollProgressRef.current = scrollY / pageHeight;
    };

    // Use multiple event types to ensure we catch scroll
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleScroll, { passive: true });
    handleScroll(); // Initial call

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleScroll);
    };
  }, []);

  useFrame(() => {
    if (groupRef.current) {
      const scrollProgress = scrollProgressRef.current;
      // Y-axis rotation (main) - full rotation per page height
      groupRef.current.rotation.y = scrollProgress * Math.PI * 2;
      // Z-axis rotation (smaller) - quarter rotation per page height
      groupRef.current.rotation.z = scrollProgress * Math.PI * 0.5;
    }
  });

  // Define the 6 faces of a cube with their corresponding textures
  const faces = [
    // Front face (positive Z)
    { position: [0, 0, 1], rotation: [0, 0, 0], normal: [0, 0, 1], texture: textures[0] },
    // Back face (negative Z)
    { position: [0, 0, -1], rotation: [0, Math.PI, 0], normal: [0, 0, -1], texture: textures[1] },
    // Right face (positive X)
    { position: [1, 0, 0], rotation: [0, Math.PI / 2, 0], normal: [1, 0, 0], texture: textures[2] },
    // Left face (negative X)
    { position: [-1, 0, 0], rotation: [0, -Math.PI / 2, 0], normal: [-1, 0, 0], texture: textures[3] },
    // Top face (positive Y)
    { position: [0, 1, 0], rotation: [-Math.PI / 2, 0, 0], normal: [0, 1, 0], texture: textures[4] },
    // Bottom face (negative Y)
    { position: [0, -1, 0], rotation: [Math.PI / 2, 0, 0], normal: [0, -1, 0], texture: textures[5] },
  ];

  return (
    <group ref={groupRef}>
      {faces.map((face, index) => (
        <CubeFace
          key={index}
          basePosition={face.position}
          rotation={face.rotation}
          normal={face.normal}
          scrollProgressRef={scrollProgressRef}
          splitThreshold={splitThreshold}
          texture={face.texture}
        />
      ))}
    </group>
  );
}

function Scene() {
  return (
    <>
      <Cube />
      <gridHelper args={[10, 10]} />
    </>
  );
}

export default Scene;

