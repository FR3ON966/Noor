# -*- coding: utf-8 -*-
"""Test Noor's intelligence - greetings, questions, memory"""
import httpx, sys, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8000'
conv_id = None

tests = [
    ("تحية", "السلام عليكم"),
    ("هوية", "انتي منو؟"),
    ("حال", "كيف حالك"),
    ("سؤال أكاديمي", "ما هي أقسام كلية الهندسة؟"),
    ("متابعة", "وكم مدة الدراسة فيها؟"),
    ("سؤال تسجيل", "كيف أسجل كطالب جديد؟"),
    ("شكر", "شكراً جزيلاً"),
    ("وداع", "مع السلامة"),
]

for label, q in tests:
    print(f"\n{'='*60}")
    print(f"[{label}] Q: {q}")
    print('='*60)
    start = time.time()
    try:
        r = httpx.post(
            f'{BASE}/api/chat/',
            json={'message': q, 'conversation_id': conv_id, 'language': 'auto'},
            timeout=120.0
        )
        data = r.json()
        conv_id = data.get('conversation_id', conv_id)
        ans = data.get('answer', 'N/A')
        conf = data.get('confidence_score', 0)
        t_ms = data.get('response_time_ms', int((time.time()-start)*1000))
        print(f"A: {ans}")
        print(f"⏱️ {t_ms}ms | 🎯 {conf*100:.0f}%")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n\n✅ ALL TESTS DONE!")
