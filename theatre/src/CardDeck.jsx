import React, { useRef, useEffect } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { TextureLoader, Vector3 } from 'three';

// Individual card component
function Card({ index, totalCards, texture, scrollProgressRef, delay }) {
  const meshRef = useRef(null);
  const cardWidth = 1.2;
  const cardHeight = 1.8;
  const spreadRadius = 5;
  const cardAngle = (Math.PI * 0.7) / (totalCards - 1); // 70 degree spread
  const startAngle = -Math.PI * 0.35; // Start 35 degrees to the left
  
  useFrame(() => {
    if (meshRef.current) {
      // Read current scroll progress from ref
      const animationProgress = scrollProgressRef.current;
      
      // Staggered animation - each card starts slightly after the previous
      const cardProgress = Math.max(0, Math.min(1, (animationProgress - delay) / Math.max(0.01, 1 - delay)));
      
      // Calculate the target position in a fan spread
      const angle = startAngle + (index * cardAngle);
      const easedProgress = cardProgress < 1 ? 1 - Math.pow(1 - cardProgress, 3) : 1; // Ease out cubic
      
      const targetX = Math.sin(angle) * spreadRadius * easedProgress;
      const targetZ = Math.cos(angle) * spreadRadius * easedProgress;
      const targetY = 0.02 + (0.01 * index * easedProgress); // Slight vertical offset
      
      // Smooth animation to target position
      meshRef.current.position.x += (targetX - meshRef.current.position.x) * 0.15;
      meshRef.current.position.z += (targetZ - meshRef.current.position.z) * 0.15;
      meshRef.current.position.y += (targetY - meshRef.current.position.y) * 0.15;
      
      // Rotate card to face outward in the fan
      const targetRotationY = angle * easedProgress;
      meshRef.current.rotation.y += (targetRotationY - meshRef.current.rotation.y) * 0.15;
      
      // Slight tilt for realism - cards lean slightly
      const targetRotationX = Math.sin(angle) * 0.15 * easedProgress;
      const targetRotationZ = Math.cos(angle) * 0.08 * easedProgress;
      meshRef.current.rotation.x += (targetRotationX - meshRef.current.rotation.x) * 0.15;
      meshRef.current.rotation.z += (targetRotationZ - meshRef.current.rotation.z) * 0.15;
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0.02 + index * 0.01, 0]}>
      <boxGeometry args={[cardWidth, cardHeight, 0.05]} />
      <meshStandardMaterial map={texture} />
    </mesh>
  );
}

function CardDeck() {
  const groupRef = useRef(null);
  const scrollProgressRef = useRef(0);

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
      scrollProgressRef.current = Math.min(scrollY / pageHeight, 1); // Clamp to 0-1
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

  return (
    <group ref={groupRef}>
      {textures.map((texture, index) => {
        // Stagger the start of each card for a cascading effect
        const delay = index * 0.1; // Each card starts 10% later
        return (
          <Card
            key={index}
            index={index}
            totalCards={textures.length}
            texture={texture}
            scrollProgressRef={scrollProgressRef}
            delay={delay}
          />
        );
      })}
    </group>
  );
}

export default CardDeck;

