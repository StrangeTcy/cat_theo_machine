import hyge.main
import hyge.runtime
rt = hyge.runtime.boot_from_packs(hyge.main.PACK_PATHS, hyge.main._runtime_namespace())
s = rt.summary()
print('PACK_RUNTIME_LOAD_OK')
print('loaded pack count:', s.get('pack_count', 'N/A'))
print('rule_count:', s.get('rule_count', 'N/A'))
