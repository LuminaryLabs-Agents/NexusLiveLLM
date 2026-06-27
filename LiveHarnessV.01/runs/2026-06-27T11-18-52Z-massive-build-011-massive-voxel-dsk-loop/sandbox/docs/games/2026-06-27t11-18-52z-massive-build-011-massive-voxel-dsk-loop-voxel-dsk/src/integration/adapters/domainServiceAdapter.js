export const domainServiceAdapter = {
  kit: "nexusrealtime.domain-service-kit",
  expectedState: ["domainTrace", "appliedCommandIds"],
  fallback: "src/domains/buildBreakDomain.js",
  proof(state) { return Array.isArray(state?.buildBreak?.domainTrace) && Array.isArray(state?.buildBreak?.appliedCommandIds); }
};
