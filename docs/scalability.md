# Scalability

Target one million simultaneously connected users, with an assumed 10% active fraction and 0.2 API requests per active user per second: 20,000 requests/second sustained and 40,000 burst. These are planning assumptions, not test results.

## Future design envelope

Target one million simultaneously connected users, with an assumed 10% active fraction and 0.2 API requests per active user per second: 20,000 requests/second sustained and 40,000 burst. These are planning assumptions, not test results.

## Architecture stages

Progress from a measured single-host core to stateless replicas, bounded connection pools and separate gateways; then regional cells, tenant routing, private object storage and partitioning justified by query evidence.

## Qualification and funding

Test 1K, 10K, 100K and 1M connections with realistic write ratios, tenant skew, reconnect storms and failure recovery. Size services from measured throughput and target utilization. Startup free plans do not fund the full target envelope.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).
