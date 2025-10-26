import http from 'k6/http';
import { check, sleep } from 'k6';

// Параметри середовища (можеш задавати через $env:BASE_URL і $env:GROUP у PowerShell)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const GROUP = __ENV.GROUP || 'КС-21';

// Навантажувальний профіль (такий, як у тебе був приблизно: до 30 VU ~1м40с)
export const options = {
  stages: [
    { duration: '20s', target: 10 },
    { duration: '40s', target: 30 },
    { duration: '40s', target: 30 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    checks: ['rate>0.99'],
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  // 1) Логін
  const loginRes = http.post(
    `${BASE_URL}/api/login`,
    JSON.stringify({ user: 'tester' }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(loginRes, {
    'login 200': (r) => r.status === 200,
  });

  // 2) Розклад (ОБОВʼЯЗКОВО кодуємо кирилицю!)
  const url = `${BASE_URL}/api/schedule?group=${encodeURIComponent(GROUP)}`;
  const schedRes = http.get(url, { tags: { name: 'schedule' } });

  if (__ITER < 3) {
    console.log('schedule status:', schedRes.status);
    console.log('schedule body sample:', (schedRes.body || '').slice(0, 200));
  }

  check(schedRes, {
    'schedule 200': (r) => r.status === 200,
  });

  let data = null;
  try {
    data = schedRes.json();
  } catch (e) {
    // залишимо data = null
  }

  check(data, {
    'items non-empty': (d) => d && Array.isArray(d.items) && d.items.length > 0,
  });

  sleep(1);
}
