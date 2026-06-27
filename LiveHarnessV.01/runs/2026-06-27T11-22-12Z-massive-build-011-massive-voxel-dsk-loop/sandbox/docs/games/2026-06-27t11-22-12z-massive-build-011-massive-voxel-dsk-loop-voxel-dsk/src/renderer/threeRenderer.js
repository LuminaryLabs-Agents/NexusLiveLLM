import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { createMaterials } from "./materials.js";
import { createCameraRig } from "./cameraRig.js";
export function createThreeRenderer({ canvas, worldLoader, movement }) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9dd3ff); scene.fog = new THREE.Fog(0x9dd3ff, 48, 170);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 480);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setSize(innerWidth, innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x3b6740, 1.35)); const sun = new THREE.DirectionalLight(0xffffff, 1.65); sun.position.set(32, 60, 20); scene.add(sun);
  const geometry = new THREE.BoxGeometry(1, 1, 1); const materials = createMaterials(THREE); const group = new THREE.Group(); scene.add(group); const rig = createCameraRig(camera); let lastRevision = -1; let visibleBlocks = 0;
  function rebuild(force = false) { const revision = worldLoader.getRevision(); if (!force && revision === lastRevision) return; lastRevision = revision; group.clear(); const buckets = new Map(); for (const block of worldLoader.getVisibleBlocks()) { if (!buckets.has(block.blockId)) buckets.set(block.blockId, []); buckets.get(block.blockId).push(block); } visibleBlocks = 0; for (const [blockId, blocks] of buckets) { visibleBlocks += blocks.length; const mesh = new THREE.InstancedMesh(geometry, materials[blockId], blocks.length); const helper = new THREE.Object3D(); blocks.forEach((block, index) => { helper.position.set(block.x, block.y, block.z); helper.updateMatrix(); mesh.setMatrixAt(index, helper.matrix); }); group.add(mesh); } }
  function draw() { rig.update(movement.getPlayer()); renderer.render(scene, camera); }
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  function getForwardTarget(distance = 5) { const p = movement.getPlayer(); const horiz = Math.cos(p.pitch); const x = Math.round(p.x + Math.sin(p.yaw) * horiz * distance); const z = Math.round(p.z - Math.cos(p.yaw) * horiz * distance); const y = Math.max(0, Math.round(p.y + Math.sin(-p.pitch) * distance - 2)); return { x, y, z }; }
  addEventListener("resize", resize);
  return { draw, rebuild, resize, getForwardTarget, getState() { return { visibleGroups: group.children.length, visibleBlocks, lastRevision, fog: true }; } };
}
