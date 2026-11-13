# Blind semantic review summary

**Result:** 31 selected cells reviewed; 31 accept-current, 0 correction, 0 refinement, 0 hold. Confidence is high for 28 cells and moderate for 3 cells.

## Scope and evidence

- Candidate-free packet: `chaptarrng-pr190-review-gap-packet-20261103`.
- Exact head: `580538d38f92e0ec005366ff6bea3f2634400c2e`; tree: `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`.
- Reviewed all 24 locale cells for the corrected source messages at source positions 654 and 695. The packet says both corrections match the live source hashes; current caller snapshots show the SABnzbd validation instruction and Mailgun test-send failure.
- Reviewed all 7 selected changed catalog cells. Caller context identifies a Home Assistant discovery checkbox, Discord/Slack renamed headings, a Discord links field, and Home Assistant missing-books and health sensors.
- The packet contains 84 locale snapshots in total; 53 context-only rows informed cross-locale comparison and were not counted as reviewed selections.
- Packet integrity: every entry in the input `SHA256SUMS` verified successfully.

## Decision counts

| Selection group | Cells | Recommendation |
|---|---:|---|
| Corrected source position 654 | 12 | Accept current |
| Corrected source position 695 | 12 | Accept current |
| Changed existing catalog cells | 7 | Accept current |
| **Total** | **31** | **31 accept-current** |

All current targets preserve the source meaning in caller context. For source 654, every locale retains the exact `Check before download` option label and `SABnzbd` name. For source 695, every locale retains `Mailgun`. Hindi Home Assistant Discovery retains `Home Assistant`; the other selected labels have no protected literals. No selected source or target contains interpolation placeholders.

## Per-cell index

| Source ID | Locale | Decision | Confidence | Current target SHA-256 |
|---|---|---|---|---|
| `server.message.m783307436ce0` | ar | accept-current | high | `51bbb5c467b9ac276b386d48e17ce57436226e0146a0ed875ad93dace344b1b5` |
| `server.message.m843e64bf5198` | ar | accept-current | high | `f9f9334dd0d9c6edb9de34c97dde497b8154dd296b5935ea732b9e0d25f9155e` |
| `server.message.m783307436ce0` | de | accept-current | high | `f088d34700c1f3666c1f677a5dd4c010967ebb7377c4f375c11392faf8492304` |
| `server.message.m843e64bf5198` | de | accept-current | high | `d1f0280932ac27481636c595079bab3652700c622272d78ffe9aad765ca17e32` |
| `server.message.m783307436ce0` | es | accept-current | high | `5d5dbecefe5f2900990d84fd61bc1e5b2e7e61ce828044e59d2a78db989c71e7` |
| `server.message.m843e64bf5198` | es | accept-current | high | `85357cdf9773e3aa1e5c4c4d1b976b7a465f451c5d24b9b6aa0af47322520c59` |
| `server.message.m783307436ce0` | fr | accept-current | high | `dcfabbdbffad5a52b14a5404182d0a806c5337f14662a15c9083e7d086e56eaf` |
| `server.message.m843e64bf5198` | fr | accept-current | high | `563c7478670e521af493dd484941aaa8b8096463b5605dbe7cd766e20075cb71` |
| `server.message.m783307436ce0` | hi | accept-current | high | `91a145036b7a5db93436901bcbbd79f038fc437d8d139a34821a707bbf16bd52` |
| `server.message.m843e64bf5198` | hi | accept-current | high | `31befba3f1154958a07600d6cecdaf05ce74763a1bf6b54856ebd76ec8af13e8` |
| `MqttGatewayPublishHomeAssistantDiscovery` | hi | accept-current | moderate | `039092da6a14c7a953d8159226fcc7c6796243d8ed0fc863d9ac34b48cb5d10c` |
| `notification.heading.renamed` | hi | accept-current | high | `aacf37b1c7b3553442c24fb0dea9781ccf5babf28e8d2800e3b14194f97d3761` |
| `server.message.m783307436ce0` | id | accept-current | high | `267d9ca3066746b1efdb0e7c0b35000f1e7b95eccf11340fdc01f3a7191e11b6` |
| `server.message.m843e64bf5198` | id | accept-current | high | `2cb307e332a1c4e7f1d03758aba7fb7b51ef65c7e3b6a3934f4288450dce59b3` |
| `notification.field.links` | id | accept-current | high | `cfbb49891e9da0105a9b55fe6c0716030162643ad8c54dfc2f7e3f6e617397ba` |
| `server.message.m783307436ce0` | ja | accept-current | high | `89bd5c7abe4bc1cd5cd37f120ae07bcd2edf16aa884512af7518a0a40cb9004c` |
| `server.message.m843e64bf5198` | ja | accept-current | high | `1933044aae8af82e584d9dad5a182da6f5b3823865ae28b6818b0a5cc6490906` |
| `notification.sensor.missingBooks` | ja | accept-current | moderate | `4b9dfc415c03ee56312ec1d8f43fcfbe9d4acdd3a234ba26b31797ab3b68450f` |
| `server.message.m783307436ce0` | ko | accept-current | high | `bcf0b7cf028cc56e242c86a9b43b9e680bcb31414870925caf371533c2c8830e` |
| `server.message.m843e64bf5198` | ko | accept-current | high | `8b69997224b279c76155ae02568a0743237c1b4926423b26d191a9dce6b5cdb4` |
| `notification.sensor.health` | ko | accept-current | high | `58770e1edfd4427b758cf070ce3315cdb0cfe41e03045a1273d484cdbb9e6dab` |
| `server.message.m783307436ce0` | pt-BR | accept-current | high | `bf956d77cd80a82dd5e087c55b728f53660287b4cf3ef6252a7abf17f04079d7` |
| `server.message.m843e64bf5198` | pt-BR | accept-current | high | `37a774ab977fd208dcbb82eeb34724e986656ba5b02626d854af477f86aff911` |
| `server.message.m783307436ce0` | vi | accept-current | high | `6538f9c4768e53c03a58bacd6154f62db3255ab68105f79c962504593badbfbe` |
| `server.message.m843e64bf5198` | vi | accept-current | high | `2da3cd83aa6f839a260be589fb353032e5eed1587f038f45d4bb806761d89b2c` |
| `server.message.m783307436ce0` | zh-Hans | accept-current | high | `177c72ad5f3f853eb376bb62e3470221be982f53389727aea32a991dcaee9fa9` |
| `server.message.m843e64bf5198` | zh-Hans | accept-current | high | `a14e6459434010b5d6fec39d2c535debdd862f2ce1bd2691275ab104e9c94928` |
| `notification.heading.renamed` | zh-Hans | accept-current | high | `27586f180db1c8124711ada4b363c798caac53a1ab1a1fe68408b82d98c3213e` |
| `server.message.m783307436ce0` | zh-Hant | accept-current | high | `4105c1fd90d9f585a6e30c7dd147646b692913efebd53e1fcdec6f58455a1a77` |
| `server.message.m843e64bf5198` | zh-Hant | accept-current | high | `a502f394b8dce3159fc6b42546c631d41a65fd6e8f40273b7ec624b9b9ee92e2` |
| `notification.heading.renamed` | zh-Hant | accept-current | moderate | `e074bd33bd7b523769002c41b45db4b6521be9b3e3812c6cf0186dd490828e79` |

Per-cell current/recommended text, rationale, evidence pins, protected-literal checks, placeholder checks, and both hashes are in `ledger.jsonl`.
