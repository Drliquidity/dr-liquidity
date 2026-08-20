/* ============================================
   DR LIQUIDITY — Liquid Wave 3D Scene
   Custom shader-based flowing wave surface
   ============================================ */
(function () {
  if (typeof THREE === 'undefined') return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Create canvas
  const canvas = document.createElement('canvas');
  canvas.id = 'three-canvas';
  document.body.appendChild(canvas);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(
    55,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(0, 3, 9);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
  });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);

  // ========== LIQUID WAVE SURFACE ==========
  const waveGeo = new THREE.PlaneGeometry(40, 25, 100, 60);

  // Custom vertex shader — animated wave with mouse distortion
  const waveVertex = `
    uniform float uTime;
    uniform vec2 uMouse;
    varying vec2 vUv;
    varying float vElevation;

    void main() {
      vUv = uv;
      vec3 pos = position;

      // Multi-layer wave
      float wave1 = sin(pos.x * 0.5 + uTime * 0.8) * 0.6;
      float wave2 = sin(pos.x * 1.2 - uTime * 0.6) * 0.3;
      float wave3 = sin(pos.y * 0.8 + uTime * 0.5) * 0.4;
      float wave4 = cos(pos.x * 0.3 + pos.y * 0.4 + uTime * 0.4) * 0.5;

      float elevation = wave1 + wave2 + wave3 + wave4;

      // Mouse ripple
      float dist = distance(pos.xy, uMouse * 20.0);
      elevation += sin(dist * 1.5 - uTime * 2.0) * 0.4 / (dist * 0.5 + 1.0);

      pos.z = elevation;
      vElevation = elevation;

      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `;

  // Custom fragment shader — green gradient based on elevation
  const waveFragment = `
    uniform float uTime;
    uniform vec2 uMouse;
    varying vec2 vUv;
    varying float vElevation;

    void main() {
      // Green palette: deep to bright
      vec3 deepGreen = vec3(0.039, 0.208, 0.125);    // #0a3520 (premium deep)
      vec3 midGreen = vec3(0.078, 0.353, 0.212);     // #145a36 (premium primary)
      vec3 lightGreen = vec3(0.161, 0.569, 0.337);   // #299156 (premium accent)
      vec3 highlight = vec3(0.063, 0.725, 0.506);    // #10b981 (emerald pop)

      float t = (vElevation + 1.5) / 3.0;
      t = clamp(t, 0.0, 1.0);

      vec3 color = mix(deepGreen, midGreen, smoothstep(0.0, 0.5, t));
      color = mix(color, lightGreen, smoothstep(0.4, 0.8, t));
      color = mix(color, highlight, smoothstep(0.8, 1.0, t));

      // Mouse highlight
      float mouseDist = distance(vUv, uMouse * 0.5 + 0.5);
      color += (1.0 - smoothstep(0.0, 0.2, mouseDist)) * vec3(0.063, 0.725, 0.506);

      // Fade edges
      float edge = 1.0 - smoothstep(0.4, 0.5, distance(vUv, vec2(0.5)));
      float alpha = t * 0.7 + 0.1;
      alpha *= edge;

      gl_FragColor = vec4(color, alpha);
    }
  `;

  const waveUniforms = {
    uTime: { value: 0 },
    uMouse: { value: new THREE.Vector2(0, 0) },
  };

  const waveMat = new THREE.ShaderMaterial({
    vertexShader: waveVertex,
    fragmentShader: waveFragment,
    uniforms: waveUniforms,
    transparent: true,
    side: THREE.DoubleSide,
  });

  const wave = new THREE.Mesh(waveGeo, waveMat);
  wave.rotation.x = -Math.PI / 2.4;
  wave.position.y = -1.5;
  scene.add(wave);

  // ========== 3D TICKER CUBES (prop firm names floating) ==========
  const tickerData = ['APEX', 'TOPStep', 'TRADEIFY', 'MFF', 'LUCID', 'E8', 'FTMO'];
  const tickerGroup = new THREE.Group();
  const tickerItems = [];

  tickerData.forEach((name, i) => {
    const canvas2d = document.createElement('canvas');
    const ctx = canvas2d.getContext('2d');
    canvas2d.width = 512;
    canvas2d.height = 128;
    ctx.fillStyle = 'rgba(14, 77, 42, 0.95)';
    ctx.fillRect(0, 0, 512, 128);
    ctx.strokeStyle = '#2d8a4d';
    ctx.lineWidth = 4;
    ctx.strokeRect(2, 2, 508, 124);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 64px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(name, 256, 64);

    const texture = new THREE.CanvasTexture(canvas2d);
    const mat = new THREE.MeshBasicMaterial({ map: texture, transparent: true, opacity: 0.85 });
    const geo = new THREE.PlaneGeometry(2.5, 0.6);
    const mesh = new THREE.Mesh(geo, mat);
    const angle = (i / tickerData.length) * Math.PI * 2;
    const radius = 6;
    mesh.position.set(Math.cos(angle) * radius, Math.sin(angle) * 2, Math.sin(angle) * radius - 4);
    mesh.userData = { angle, radius, baseY: mesh.position.y, speed: 0.1 + Math.random() * 0.05 };
    tickerGroup.add(mesh);
    tickerItems.push(mesh);
  });
  scene.add(tickerGroup);

  // ========== FLOATING ORBS ==========
  const orbs = [];
  for (let i = 0; i < 8; i++) {
    const geo = new THREE.SphereGeometry(0.15 + Math.random() * 0.2, 16, 16);
    const mat = new THREE.MeshBasicMaterial({
      color: i % 2 === 0 ? 0x145a36 : 0x299156,
      transparent: true,
      opacity: 0.4 + Math.random() * 0.3,
    });
    const orb = new THREE.Mesh(geo, mat);
    orb.position.set(
      (Math.random() - 0.5) * 12,
      (Math.random() - 0.5) * 6,
      (Math.random() - 0.5) * 4 - 2
    );
    orb.userData = {
      baseX: orb.position.x,
      baseY: orb.position.y,
      speed: 0.3 + Math.random() * 0.4,
      offset: Math.random() * Math.PI * 2,
    };
    scene.add(orb);
    orbs.push(orb);
  }

  // ========== MOUSE TRACKING ==========
  const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
  window.addEventListener('mousemove', (e) => {
    mouse.tx = (e.clientX / window.innerWidth - 0.5) * 2;
    mouse.ty = (e.clientY / window.innerHeight - 0.5) * 2;
    // Update shader mouse uniform
    waveUniforms.uMouse.value.x = mouse.tx;
    waveUniforms.uMouse.value.y = -mouse.ty;
  });

  let scrollY = 0;
  window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
  });

  // ========== ANIMATION LOOP ==========
  const clock = new THREE.Clock();

  function animate() {
    const t = clock.getElapsedTime();
    waveUniforms.uTime.value = t;

    // Smooth mouse
    mouse.x += (mouse.tx - mouse.x) * 0.06;
    mouse.y += (mouse.ty - mouse.y) * 0.06;

    // Camera subtle motion
    camera.position.x = mouse.x * 1.2;
    camera.position.y = 3 - mouse.y * 0.8 - scrollY * 0.001;
    camera.lookAt(0, 0, 0);

    // Wave subtle motion
    wave.position.z = mouse.x * 0.3;

    // Ticker rotation
    tickerGroup.rotation.y = t * 0.1 + mouse.x * 0.3;
    tickerItems.forEach((item) => {
      item.lookAt(camera.position);
      item.position.y = item.userData.baseY + Math.sin(t * item.userData.speed) * 0.3;
    });

    // Orbs float
    orbs.forEach((orb) => {
      orb.position.x = orb.userData.baseX + Math.sin(t * orb.userData.speed + orb.userData.offset) * 0.5;
      orb.position.y = orb.userData.baseY + Math.cos(t * orb.userData.speed * 0.7) * 0.3;
    });

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) renderer.setAnimationLoop(null);
    else animate();
  });
})();
