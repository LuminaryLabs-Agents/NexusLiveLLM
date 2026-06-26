import assert from "node:assert/strict";
import { createCommandQueue } from "../src/runtime/commandQueue.js";
const queue = createCommandQueue();
assert.equal(queue.markApplied("cmd-1"), true);
assert.equal(queue.markApplied("cmd-1"), false);
console.log("smoke passed");
