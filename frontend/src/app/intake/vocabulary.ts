// Mirrors backend/app/simulation/config.py's closed vocabulary. The matching
// engine does exact string comparisons, so intake has to offer the same
// values the synthetic providers were generated with, not free text, or a
// submission would never find an eligible provider.
export const STATES = ["CA", "NY", "TX", "FL", "IL", "WA", "MA", "GA"] as const;
export const PAYERS = ["Aetna", "Cigna", "UnitedHealthcare", "BlueCross", "Humana", "Medicaid"] as const;
export const SPECIALTIES = [
  "anxiety",
  "depression",
  "trauma",
  "adhd",
  "couples",
  "ocd",
  "eating_disorders",
  "substance_use",
] as const;
export const LANGUAGES = ["en", "es", "zh", "vi"] as const;
export const MODALITIES = ["video", "in_person"] as const;
