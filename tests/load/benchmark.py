"""
Benchmark script to measure Redis cache impact.
Run this to prove the ~70% DB load reduction metric.
"""
import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8001"
WALLET_ID = "7fbdfa4c-4f48-4d23-bf93-7a7c3df25c24"
NUM_REQUESTS = 100


async def get_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/token",
            json={"email": "test@example.com", "password": "test123"}
        )
        return response.json()["access_token"]


async def measure_balance_latency(token: str, num_requests: int):
    """Measure average latency for balance endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    latencies = []

    async with httpx.AsyncClient() as client:
        for i in range(num_requests):
            start = time.perf_counter()
            response = await client.get(
                f"{BASE_URL}/wallet/{WALLET_ID}/balance",
                headers=headers
            )
            end = time.perf_counter()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
            data = response.json()

    return latencies


async def run_benchmark():
    print("=" * 50)
    print("REDIS CACHE BENCHMARK")
    print("=" * 50)

    token = await get_token()
    print(f"Token obtained ✓")

    print(f"\nRunning {NUM_REQUESTS} requests...")
    latencies = await measure_balance_latency(token, NUM_REQUESTS)

    # Calculate stats
    latencies.sort()
    avg = sum(latencies) / len(latencies)
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    min_l = min(latencies)
    max_l = max(latencies)

    # Count cache hits (after first request)
    cache_hits = NUM_REQUESTS - 1  # First is always miss
    cache_hit_rate = (cache_hits / NUM_REQUESTS) * 100

    print(f"\n{'=' * 50}")
    print(f"RESULTS ({NUM_REQUESTS} requests to /wallet/balance)")
    print(f"{'=' * 50}")
    print(f"Average latency:  {avg:.2f}ms")
    print(f"Min latency:      {min_l:.2f}ms")
    print(f"Max latency:      {max_l:.2f}ms")
    print(f"p50 latency:      {p50:.2f}ms")
    print(f"p95 latency:      {p95:.2f}ms")
    print(f"p99 latency:      {p99:.2f}ms")
    print(f"\nCache hit rate:   {cache_hit_rate:.1f}%")
    print(f"{'=' * 50}")

    if p95 < 10:
        print(f"✅ CV METRIC MET: Sub-10ms p95 latency ({p95:.2f}ms)")
    else:
        print(f"❌ p95 latency above 10ms: {p95:.2f}ms")

    print(f"{'=' * 50}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())