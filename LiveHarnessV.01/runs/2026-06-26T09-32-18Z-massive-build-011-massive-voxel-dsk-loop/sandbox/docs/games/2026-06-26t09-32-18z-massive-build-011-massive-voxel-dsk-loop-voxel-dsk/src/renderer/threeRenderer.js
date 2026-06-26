import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { createMaterials } from "./materials.js";
import { createCameraRig } from "./cameraRig.js";
export function createThreeRenderer({ canvas, blockStore, movement }) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9ed0ff); scene.fog = new THREE.Fog(0x9ed0ff, 36, 120);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 300);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setSize(innerWidth, innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x446644, 1.35)); const sun = new THREE.DirectionalLight(0xffffff, 1.7); sun.position.set(24, 40, 18); scene.add(sun);
  const geometry = new THREE.BoxGeometry(1, 1, 1); const materials = createMaterials(THREE); const group = new THREE.Group(); scene.add(group); const rig = createCameraRig(camera);
  function rebuild() { group.clear(); const buckets = new Map(); for (const block of blockStore.entries()) { if (!buckets.has(block.blockId)) buckets.set(block.blockId, []); buckets.get(block.blockId).push(block); } for (const [blockId, blocks] of buckets) { const mesh = new THREE.InstancedMesh(geometry, materials[blockId], blocks.length); const helper = new THREE.Object3D(); blocks.forEach((block, index) => { helper.position.set(block.x, block.y, block.z); helper.updateMatrix(); mesh.setMatrixAt(index, helper.matrix); }); group.add(mesh); } }
  function draw() { rig.update(movement.getPlayer()); renderer.render(scene, camera); }
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  addEventListener("resize", resize);
  return { draw, rebuild, resize, getForwardTarget(distance = 4) { const p = movement.getPlayer(); const x = Math.round(p.x + Math.sin(p.yaw) * distance); const z = Math.round(p.z - Math.cos(p.yaw) * distance); return { x, y: Math.max(1, Math.round(p.y - 3)), z }; } };
}
