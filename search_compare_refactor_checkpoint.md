# search_compare_refactor_checkpoint

Current known-good commands before/through pass 1:
- python -m cat_theo_machine.testsuite
- python -m cat_theo_machine.test_actual_searchdfs
- python -m cat_theo_machine.main cold debug

Current expected prompt behavior:
- mode workers stop at success-plan-found when deferred comparison mode is enabled
- parent prints an explicit approval prompt before derivation replay/save

Current heavy-memory behavior:
- search is parallel across mode workers
- derivation replay/save is deferred to approval path
- partial checkpoints are smaller than full worker snapshots
