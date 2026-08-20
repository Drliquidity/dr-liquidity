/* ============================================
   DR LIQUIDITY — Three.js Hero Scene
   ============================================ */
(function () {
  if (typeof THREE === 'undefined') {
    console.warn('Three.js not loaded, skipping 3D scene');
    return;
  }

  // Respect reduced motion
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Create canvas
  const canvas = document.createElement('canvas');
  canvas.id = 'three-canvas';
  document.body.appendChild(canvas);

  // Scene setup
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0xffffff, 8, 30);

  const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(0, 0, 8);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
  });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);

  // Brand color palette
  const GREEN_DARK = 0x0a3d22;
  const GREEN = 0x0e4d2a;
  const GREEN_MID = 0x1f6e3c;
  const GREEN_LIGHT = 0x2d8a4d;

  // === Main shape: rotating icosahedron with wireframe + solid mix ===
  const icoGeo = new THREE.IcosahedronGeometry(2.2, 1);
  const icoMat = new THREE.MeshBasicMaterial({
    color: GREEN,
    wireframe: true,
    transparent: true,
    opacity: 0.35,
  });
  const ico = new THREE.Mesh(icoGeo, icoMat);
  ico.position.set(2.5, 0, -2);
  scene.add(ico);

  // Inner glow sphere
  const glowGeo = new THREE.SphereGeometry(1.4, 32, 32);
  const glowMat = new THREE.MeshBasicMaterial({
    color: GREEN_DARK,
    transparent: true,
    opacity: 0.15,
  });
  const glow = new THREE.Mesh(glowGeo, glowMat);
  ico.add(glow);

  // === Secondary shape: torus knot on the left ===
  const torusGeo = new THREE.TorusKnotGeometry(1.2, 0.35, 100, 16);
  const torusMat = new THREE.MeshBasicMaterial({
    color: GREEN_MID,
    wireframe: true,
    transparent: true,
    opacity: 0.25,
  });
  const torus = new THREE.Mesh(torusGeo, torusMat);
  torus.position.set(-3, -1, -3);
  scene.add(torus);

  // === Floating cubes (data grid feel) ===
  const cubeGroup = new THREE.Group();
  for (let i = 0; i < 12; i++) {
    const size = Math.random() * 0.15 + 0.08;
    const cubeGeo = new THREE.BoxGeometry(size, size, size);
    const cubeMat = new THREE.MeshBasicMaterial({
      color: i % 3 === 0 ? GREEN_LIGHT : GREEN,
      wireframe: true,
      transparent: true,
      opacity: 0.5,
    });
    const cube = new THREE.Mesh(cubeGeo, cubeMat);
    const angle = (i / 12) * Math.PI * 2;
    const radius = 4 + Math.random() * 2;
    cube.position.set(
      Math.cos(angle) * radius,
      (Math.random() - 0.5) * 6,
      Math.sin(angle) * radius - 2
    );
    cube.userData = {
      baseY: cube.position.y,
      speed: 0.5 + Math.random() * 0.5,
      offset: Math.random() * Math.PI * 2,
    };
    cubeGroup.add(cube);
  }
  scene.add(cubeGroup);

  // === Particle field ===
  const particleCount = 200;
  const particleGeo = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 20;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 12;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 10 - 3;
  }
  particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const particleMat = new THREE.PointsMaterial({
    color: GREEN,
    size: 0.04,
    transparent: true,
    opacity: 0.6,
    sizeAttenuation: true,
  });
  const particles = new THREE.Points(particleGeo, particleMat);
  scene.add(particles);

  // === Grid floor (subtle perspective lines) ===
  const grid = new THREE.GridHelper(20, 20, GREEN, GREEN);
  grid.material.opacity = 0.08;
  grid.material.transparent = true;
  grid.position.y = -4;
  scene.add(grid);

  // === Mouse tracking ===
  const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
  window.addEventListener('mousemove', (e) => {
    mouse.tx = (e.clientX / window.innerWidth - 0.5) * 2;
    mouse.ty = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  // === Scroll tracking for parallax ===
  let scrollY = 0;
  window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
  });

  // === Animation loop ===
  const clock = new THREE.Clock();
  function animate() {
    const t = clock.getElapsedTime();

    // Smooth mouse follow
    mouse.x += (mouse.tx - mouse.x) * 0.05;
    mouse.y += (mouse.ty - mouse.y) * 0.05;

    // Icosahedron rotation
    ico.rotation.x = t * 0.15;
    ico.rotation.y = t * 0.2;
    ico.position.y = Math.sin(t * 0.5) * 0.3;
    ico.position.x = 2.5 + mouse.x * 0.5;

    // Torus rotation
    torus.rotation.x = t * 0.3;
    torus.rotation.y = t * 0.2;
    torus.position.y = -1 + Math.cos(t * 0.4) * 0.2 - scrollY * 0.001;
    torus.position.x = -3 + mouse.x * 0.3;

    // Cubes float
    cubeGroup.children.forEach((cube) => {
      cube.position.y = cube.userData.baseY + Math.sin(t * cube.userData.speed + cube.userData.offset) * 0.3;
      cube.rotation.x = t * 0.5;
      cube.rotation.y = t * 0.3;
    });

    // Particle drift
    particles.rotation.y = t * 0.02;
    particles.rotation.x = mouse.y * 0.1;
    const pos = particles.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const iy = pos.getY(i);
      pos.setY(i, iy + Math.sin(t + i) * 0.0008);
    }
    pos.needsUpdate = true;

    // Camera follows mouse subtly
    camera.position.x = mouse.x * 0.5;
    camera.position.y = -mouse.y * 0.3;
    camera.lookAt(0, 0, 0);

    // Scroll-based camera zoom
    const targetZ = 8 + scrollY * 0.002;
    camera.position.z += (targetZ - camera.position.z) * 0.05;

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();

  // === Resize ===
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Pause when tab hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) renderer.setAnimationLoop(null);
    else animate();
  });
})();
