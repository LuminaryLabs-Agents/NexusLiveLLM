import { BLOCK_BY_ID } from "../data/blocks.js";
export function createMaterials(THREE) { const materials = {}; for (const block of Object.values(BLOCK_BY_ID)) { if (block.id === 0) continue; materials[block.id] = new THREE.MeshStandardMaterial({ color: block.color, roughness: 0.8, transparent: block.name === "glass", opacity: block.name === "glass" ? 0.52 : 1 }); } return materials; }
