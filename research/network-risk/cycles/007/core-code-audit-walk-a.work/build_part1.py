import json
ALL=[n['chainId'] for n in json.load(open('../../../state/networks.json'))['networks']]
OZ='docs/security/audits/OpenZeppelin_audit_core.pdf'
TOB='docs/security/audits/TrailOfBits_audit_core.pdf'
KE='docs/security/Known_Effects_of_Hook_Permissions.pdf'
WALK='eth_call with state overrides on the rpc URL of each of the 21 entries of research/network-risk/state/networks.json on 2026-11-23, script walk.py and results raw/walk.json in research/network-risk/cycles/007/core-code-audit-walk-a.work'
findings=[]
findings.append({
 "ref":"F-014",
 "title":"The two lock guards that Trail of Bits finding 3 records as its fix are absent from the source, and the synced currency check that stands in their place skips address(0), which shares its balance with an ERC-20 address on five networks",
 "chainIds":[1,10,8453,42161,4663,137,56,5042],
 "lens":"L3",
 "assumptions":["A1","A3","A12"],
 "effect":"degrade",
 "actor":"unprivileged",
 "severity":"info",
 "difference":"On Ethereum no ERC-20 address reports the PoolManager's native balance. On five of the 21 networks one does: LegacyERC20ETH at 0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000 on Optimism and Zora, 0x0000000000000000000000000000000000001010 on Polygon, the CELO token 0x471EcE3750Da237f93B8E339c536989b8978a438 on Celo and 0x3600000000000000000000000000000000000000 on Arc, where the figure is the native balance divided by 10^12. I read balanceOf(PoolManager) and eth_getBalance at one block per network and they agree on these five and on no candidate address of the other 16. Optimism, Polygon and Arc also have a fee controller whose collect function any account can call. Celo and Zora have no fee controller today.",
 "mechanism":"1. The report (printed page 33) describes the hazard: a fee collection between sync and settle lowers the balance, so the settle that follows credits less or reverts. Its fix review (printed page 62) records the fix as two guards: sync can be called only while the manager is unlocked, and collectProtocolFees reverts with ContractUnlocked while the manager is unlocked. 2. The source has neither guard. sync carries no modifier (src/PoolManager.sol:279-288). collectProtocolFees checks the caller and then reverts only when the currency is nonzero and equals the synced currency (src/ProtocolFees.sol:48-52). _isUnlocked is declared at src/ProtocolFees.sol:60 and implemented at src/PoolManager.sol:392-394 and has no caller. The interface still says the function reverts if the contract is unlocked (src/interfaces/IProtocolFees.sol:40) and declares ProtocolFeeCurrencySynced and no ContractUnlocked error (line 17). The tests of the repository expect the source behaviour in both lock states (test/PoolManager.t.sol:1001-1039) and call sync while locked (test/Sync.t.sol:36-41). 3. The check that replaced the guards closes the report's case when the collected id is the synced id. It compares ids and exempts address(0) with the comment that native settle uses msg.value. That reasoning assumes the native balance has no second id (A3). 4. Where a native face exists and a controller can be triggered, the report's sequence runs again across two ids: sync(face), collection of native fees, settle. My walk on the deployed PoolManagers of Optimism (block 159,929,377), Polygon (97,834,382) and Arc (32,774,161), with a stub placed at the controller address by state override, gave the same three answers on each: collection of the face id reverted with ProtocolFeeCurrencySynced, collection of address(0) succeeded inside the unlock while the face was synced and paid out the accrued native fees (0.0407 ETH, 714.3 POL and 53.28 USDC), and the settle that followed reverted with a Panic from the checked subtraction at src/PoolManager.sol:360. On the other five controller networks the same walk with a stub token that returns the native balance of its argument gave the same answers. 5. A separate eth_call of collect((address,uint256)[]) with one entry for address(0) from an arbitrary account succeeded on all eight controllers, and each controller names one fixed TOKEN_JAR. 6. I traced who pays. Collection lowers protocolFeesAccrued by a checked subtraction before the transfer (src/ProtocolFees.sol:54-56), writes no delta and no transient slot, and pays the recipient the controller names. The lower balance reduces the credit of the account that holds the face bracket in that same transaction, or reverts its settle. A payer that syncs, transfers and settles without calling other code in between cannot be interleaved. The caller of collect gains nothing. 7. Two further effects follow from the absent guards. Any code that runs earlier in a shared transaction can leave sync(X) and make a later collection of X revert (src/ProtocolFees.sol:49-51), which contradicts the report's invariant UNI-ACTION-6 as worded (collectProtocolFees must not revert on valid input). The same stale sync makes a later native settle with value revert, which the ledger holds as F-071.",
 "impact":"No loss of pool funds and no lasting freeze found. The account that syncs a native face and lets a native fee collection run before its settle loses credit equal to the collected amount or has its transaction reverted. Fee collection of a currency can be made to revert by an earlier sync in the same transaction. The finding extends F-014 from Ethereum to the eight networks with a controller and ties it to the audit record.",
 "preconditions":"A fee controller that any account can trigger (Ethereum, Optimism, Base, Arbitrum One, Robinhood Chain, Polygon, BNB Smart Chain and Arc today). For the two id case also an address that reports the native balance (Optimism, Polygon and Arc today, and Celo and Zora once the owner sets a controller there). The affected party must itself hold a sync of the face while the collection runs.",
 "mitigations":"Restore the lock check that the interface comment describes, or make the synced check cover address(0) as well. Contracts that harvest fees and settle in one transaction should collect before they sync. Routers should call sync themselves before each payment, native payments included.",
 "coreRefs":["src/ProtocolFees.sol:44-60","src/PoolManager.sol:279-288","src/PoolManager.sol:349-365","src/PoolManager.sol:391-394","src/interfaces/IProtocolFees.sol:13-17","src/interfaces/IProtocolFees.sol:39-47"],
 "sources":[
  {"url":TOB+":33","supports":"Printed page 33, finding 3: collection between sync and settle counts against the settler, and the short term recommendation is a guard on collectProtocolFees while unlocked and a guard on sync"},
  {"url":TOB+":62","supports":"Printed page 62, fix review: a guard was added to sync so that it can only be called when unlocked, and collectProtocolFees reverts with ContractUnlocked when unlocked"},
  {"url":"src/ProtocolFees.sol:48","supports":"Lines 48 to 52 check the caller and the synced ERC-20 only, address(0) is exempt, and no lock is read"},
  {"url":"src/PoolManager.sol:279","supports":"sync has no onlyWhenUnlocked modifier"},
  {"url":"test/PoolManager.t.sol:1001","supports":"Lines 1001 to 1039: the tests expect ProtocolFeeCurrencySynced with the manager locked and unlocked"},
  {"url":WALK,"supports":"On Optimism, Polygon and Arc a native fee collection succeeded inside an unlock while the real native face was synced and the next settle reverted with Panic; on all eight controller networks the same held with a stub face; sync succeeded while locked on all 21"},
  {"url":"eth_call of collect((address,uint256)[]) from 0xe0a0000000000000000000000000000000000e0a on the rpc URLs of chain ids 1, 10, 8453, 42161, 4663, 137, 56 and 5042 on 2026-11-23, script collect.py, results raw/collect.json in the work directory of this unit","supports":"collect succeeds for an arbitrary caller on all eight fee controllers, and TOKEN_JAR() returns one fixed address on each"},
  {"url":"eth_getBalance and eth_call balanceOf at one block per network on the 21 rpc URLs on 2026-11-23, script faces.py, results raw/faces.json in the work directory of this unit","supports":"The five addresses that report the PoolManager's native balance, and the absence of such an answer from the same candidates on the other 16 networks"}],
 "evidence":"primary"})
findings.append({
 "ref":"new",
 "title":"OpenZeppelin CR-01 records that noDelegateCall was added to all relevant external functions, and the source carries it on the four pool functions only",
 "chainIds":ALL,
 "lens":"L1",
 "assumptions":["A8"],
 "effect":"degrade",
 "actor":"unprivileged",
 "severity":"info",
 "difference":"None found. The guard compares address(this) with an immutable (src/NoDelegateCall.sol:24-26). Earlier cycles tested on all 21 deployed PoolManagers that a DELEGATECALL into the unguarded functions uses the storage, transient storage and balance of the calling account, and on 20 networks that an EIP-7702 account that names the PoolManager behaves the same. The Avalanche endpoint did not resolve a delegation designator.",
 "mechanism":"1. The report (page 24) says the modifier on unlock was meant to stop proxies for licence reasons, that a custom unlock that writes the same lock slot got around it, and that the team added noDelegateCall to all relevant external functions. 2. In the source the modifier sits on initialize, modifyLiquidity, swap and donate (src/PoolManager.sol:117, 148, 190, 259). unlock, sync, take, settle, settleFor, clear, mint and burn carry none (lines 104, 279, 291, 300, 305, 310, 322, 332). The test double of the repository puts it on unlock, take, settle, settleFor, mint and burn (src/test/ProxyPoolManager.sol:58, 151, 156, 163, 176, 181), and test/NoDelegateCall.t.sol:63-82 expects the revert from modifyLiquidity, swap and donate only. 3. I checked whether the gap reaches funds. A delegatecall runs the settlement functions on the lock flag, deltas, claims and balance of the calling contract. No pool can be created or used that way, because all four pool functions revert with DelegateCallNotAllowed. The PoolManager itself contains no delegatecall (search of src outside src/test). The stated purpose of the fix, keeping pool logic from running behind a proxy, is met by the four guarded functions. 4. The cleared items of cycles 1, 3 and 6 reach the same result, the last one by a test on every network.",
 "impact":"No effect on funds held by the PoolManager. A contract or delegated account that runs this code on itself exposes its own balances to flash use and to the booking of balance increases, which concerns only that account.",
 "preconditions":"None for the gap itself. An effect needs an account that chooses to run PoolManager code in its own context.",
 "mitigations":"Add the modifier to the six functions that the test double guards if the licence purpose is to cover the settlement layer as well. No change is needed for custody.",
 "coreRefs":["src/PoolManager.sol:104-114","src/PoolManager.sol:279-336","src/NoDelegateCall.sol:14-32"],
 "sources":[
  {"url":OZ+":24","supports":"CR-01: the limitation can be skipped, and the update says noDelegateCall was added to all relevant external functions"},
  {"url":"src/PoolManager.sol:117","supports":"Lines 117, 148, 190 and 259 are the only uses of the modifier"},
  {"url":"src/test/ProxyPoolManager.sol:58","supports":"The test double guards unlock, take, settle, settleFor, mint and burn at lines 58, 151, 156, 163, 176 and 181"},
  {"url":"research/network-risk/state/cleared.json: core-code-loose-guards, cycle 6","supports":"DELEGATECALL into the unguarded functions on all 21 deployed PoolManagers used the caller's storage and balance, and delegated accounts gave the same answers on 20 networks"}],
 "evidence":"primary"})
findings.append({
 "ref":"new",
 "title":"Any account can set the starting price of a pool or move the price of an empty pool for free, and core takes no price or amount bound on the first deposit (OpenZeppelin M-03, acknowledged and not resolved)",
 "chainIds":ALL,
 "lens":"L6",
 "assumptions":[],
 "effect":"siphon",
 "actor":"unprivileged",
 "severity":"low",
 "difference":"None in the code path, which is the same on Ethereum. Networks differ in who can see a pending transaction, and I fetched no source on that for the 21 networks in this session. The variant that initializes a predictable PoolKey ahead of its creator needs no view of pending transactions.",
 "mechanism":"1. initialize accepts any caller and stores the caller's price (src/PoolManager.sol:117-134, src/libraries/Pool.sol:100-107). The price is not part of the pool id (src/types/PoolId.sol:11-15), and a second initialize reverts (Pool.sol:101). Whoever is first sets the price. 2. swap has no check for liquidity. With zero liquidity in range each step returns zero amounts and moves the price to the next tick or to the limit (Pool.sol:344-437, src/libraries/SwapMath.sol:63-106), so any account can move the price of a pool without in range liquidity to any value inside the bounds for a zero delta. 3. modifyLiquidity computes the two amounts from the stored price (Pool.sol:206-236) and accepts no minimum or maximum from the caller (src/PoolManager.sol:145-184). 4. A provider that adds liquidity after the price was set away from the market deposits at that price, and the attacker then swaps against the position at the off market price. 5. Nothing in src closes this. The report records the team's answer that peripheral contracts add slippage protection. I did not read the periphery. 6. On all 21 deployed PoolManagers an eth_call of initialize from an arbitrary account for an unused PoolKey returned ticks 0, 138162, -887272 and 887271 for four prices of my choice.",
 "impact":"The first liquidity provider of a pool who adds through code without amount bounds can lose part of the deposit, up to most of its value, to the account that set the price. Pools that already hold in range liquidity are not affected, because moving their price costs the swap amounts.",
 "preconditions":"A pool that is not yet initialized or has no in range liquidity, and a provider that adds liquidity without checking the pool price or bounding the amounts. The attacker needs no role.",
 "mitigations":"Initialize and add liquidity in one transaction with amount bounds, as the report's update says the periphery does. Integrations that call modifyLiquidity themselves should read slot0 and compare the price before they add.",
 "coreRefs":["src/PoolManager.sol:117-142","src/PoolManager.sol:145-184","src/libraries/Pool.sol:100-107","src/libraries/Pool.sol:344-437"],
 "sources":[
  {"url":OZ+":13","supports":"Pages 13 and 14, M-03: front-running initialization or the first deposit, the five step scenario, and the update that the issue is acknowledged and not resolved"},
  {"url":"src/libraries/Pool.sol:344","supports":"The swap loop has no liquidity check and a step with zero liquidity moves the price with zero amounts"},
  {"url":"src/PoolManager.sol:117","supports":"initialize has no caller check and the price is an argument"},
  {"url":"eth_call of initialize from an arbitrary account on the 21 rpc URLs of research/network-risk/state/networks.json on 2026-11-23, script init.py, results raw/init.json in the work directory of this unit","supports":"A fresh pool can be initialized by any account at the lowest, the highest and two other prices on every deployed PoolManager"}],
 "evidence":"primary"})
findings.append({
 "ref":"new",
 "title":"A pool id that resembles another pool's id can be mined through the hooks field of the PoolKey, and core gives a reader nothing to tell the two pools apart (Trail of Bits finding 6, unresolved)",
 "chainIds":ALL,
 "lens":"L1",
 "assumptions":["A7"],
 "effect":"siphon",
 "actor":"pool-creator",
 "severity":"low",
 "difference":"None found. The report's method places a hook at a mined address with CREATE2. An account with a mined address and an EIP-7702 delegation serves the same purpose where delegation is live, which the ledger records as F-013.",
 "mechanism":"1. The pool id is the keccak256 hash of the five words of the PoolKey (src/types/PoolId.sol:11-15) and the hooks address is the fifth word (src/types/PoolKey.sol:11-22). 2. initialize constrains the hook address only through its low 14 bits and the dynamic fee rule (src/libraries/Hooks.sol:109-127, src/PoolManager.sol:126), so 146 bits of the address are free to vary while currencies, fee and tick spacing equal those of a known pool. 3. Core stores every pool under its full 32 byte id (src/PoolManager.sol:93), so two pools never share state. The hazard is in displays that shorten the id: a mined id can match the first and last characters of the known pool's id. 4. The attacker's pool carries the attacker's hook, which has the powers listed in the hook permissions note of this repository. 5. The fix review marks the finding unresolved, and nothing in src addresses it.",
 "impact":"A user who picks a pool by a shortened id, or an integration that matches pools by a prefix, can be led into a pool whose hook takes the swap input or blocks removal. Funds in the original pool are not touched.",
 "preconditions":"The victim must choose the attacker's pool. The attacker must author the hook.",
 "mitigations":"Interfaces should show and compare the full PoolKey with the hook address. Integrations should match pools by the full 32 byte id.",
 "coreRefs":["src/types/PoolId.sol:11-15","src/types/PoolKey.sol:11-22","src/libraries/Hooks.sol:109-127","src/PoolManager.sol:117-134"],
 "sources":[
  {"url":TOB+":39","supports":"Printed pages 39 and 40, finding 6: the four requirements of the lookalike pool and the recommendation to document it"},
  {"url":TOB+":62","supports":"Printed page 62: unresolved, the team decided not to resolve the issue"},
  {"url":"src/types/PoolId.sol:11","supports":"The id is the hash of all five PoolKey words"},
  {"url":"src/libraries/Hooks.sol:109","supports":"Only the low 14 bits and the dynamic fee rule constrain the hook address"}],
 "evidence":"primary"})
findings.append({
 "ref":"F-004",
 "title":"The repository's note on hook permissions confirms that a hook can block liquidity removal for good and can take a caller's full amounts through return deltas, and core limits these effects to the hook's own pool and to the bits of its address",
 "chainIds":ALL,
 "lens":"L1",
 "assumptions":["A7"],
 "effect":"both",
 "actor":"pool-creator",
 "severity":"medium",
 "difference":"None found in core. The note assumes the hook is the contract its author deployed. Where the code behind a hook address can change (EIP-7702 delegation, Stylus expiry on the Arbitrum family), the ledger records that separately as F-013, F-003 and F-053.",
 "mechanism":"1. The note lists 27 effects. I read each against src and found that none is prevented and each is confined. 2. Blocking: every hook call that fails or returns a wrong selector reverts the action (src/libraries/Hooks.sol:131-155). A hook with a remove flag is called for every liquidityDelta at or below zero, a fee collection with delta zero included (Hooks.sol:201-205, 232-243), and core has no path that removes liquidity without that call (src/PoolManager.sol:156, 178). The note marks this case as funds that could be permanently locked. 3. Taking: a hook with a return delta flag gets its returned amounts booked to its own address, and the caller's delta is reduced by the same amounts (Hooks.sol:222-230, 234-242, 295-313, PoolManager.sol:181-183, 224-226). Core sets no upper bound on these amounts. The one bound is that a beforeSwap delta cannot turn an exact input swap into an exact output swap or the reverse (Hooks.sol:273-279), which is why a hook can take all of the specified amount of an exact input swap and none of the specified amount of an exact output swap, as the note says. 4. Confinement: return delta flags are honoured only together with their action flag (Hooks.sol:111-120), hook deltas are booked in the two currencies of the pool the hook is attached to (PoolManager.sol:381-384), the sum of caller delta and hook delta equals the pool delta in every branch, and a hook's own calls into the PoolManager skip its hooks (Hooks.sol:171-175, 217, 253, 293). 5. Front-running, back-running, sandwiching and just in time liquidity by a hook use ordinary swap and modifyLiquidity calls from inside the callback and need no special permission in core.",
 "impact":"Liquidity providers and swappers of a pool with a hook depend on that hook for exit and for the amounts they receive. Pools without a hook and pools with another hook are not affected. This adds the repository's own statement of the hazard to F-004.",
 "preconditions":"The victim uses a pool whose hook was written, or can be changed, by the attacker.",
 "mitigations":"As the note says for each return delta case, routers should check the returned deltas against the caller's bounds. Providers should read a hook's remove path before they deposit. Nothing in core can be configured.",
 "coreRefs":["src/libraries/Hooks.sol:109-127","src/libraries/Hooks.sol:131-168","src/libraries/Hooks.sol:195-315","src/PoolManager.sol:145-227","src/PoolManager.sol:381-384"],
 "sources":[
  {"url":KE+":2","supports":"Page 2: before and after removeLiquidity can cause a revert, implying user funds could be permanently locked and fees never collected"},
  {"url":KE+":3","supports":"Pages 2 to 4: the return delta cases, with the remark that each should be checked in a router"},
  {"url":"src/libraries/Hooks.sol:201","supports":"Remove hooks run for every liquidityDelta at or below zero and a failed hook call reverts the action"},
  {"url":"src/libraries/Hooks.sol:273","supports":"The only bound on a beforeSwap delta is that the swap type cannot change"}],
 "evidence":"primary"})
json.dump({'ALL':ALL,'findings':findings},open('part1.json','w'),indent=1)
print(len(findings))
