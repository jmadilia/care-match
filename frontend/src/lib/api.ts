// 127.0.0.1 (not "localhost") avoids Node's fetch trying an IPv6 route to a
// backend that only listens on IPv4.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
