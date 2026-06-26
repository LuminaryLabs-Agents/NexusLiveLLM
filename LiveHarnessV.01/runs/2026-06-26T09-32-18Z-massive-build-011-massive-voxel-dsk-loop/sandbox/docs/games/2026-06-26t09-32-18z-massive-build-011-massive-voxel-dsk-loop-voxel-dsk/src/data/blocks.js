export const BLOCK_TYPES = {
  air: { id: 0, name: "air", color: 0x000000 },
  grass: { id: 1, name: "grass", color: 0x4faf65 },
  dirt: { id: 2, name: "dirt", color: 0x8a5a35 },
  stone: { id: 3, name: "stone", color: 0x8a93a3 },
  wood: { id: 4, name: "wood", color: 0x8b5a2b },
  glass: { id: 5, name: "glass", color: 0x84d8ff }
};
export const BLOCK_BY_ID = Object.fromEntries(Object.values(BLOCK_TYPES).map((block) => [block.id, block]));
export const PLACEABLE_BLOCKS = Object.values(BLOCK_TYPES).filter((block) => block.id !== 0);
