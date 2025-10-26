import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10, duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const token = http.post(`${BASE}/api/login`, JSON.stringify({ user: 'admin' }),
    { headers: { 'Content-Type': 'application/json' } }).json('token');

  const body = JSON.stringify({
    date: '2025-10-25', time: '09:00', title: 'Перевірка', room: '101', group: 'КС-21'
  });
  const r = http.post(`${BASE}/api/add_event?token=${token}`, body,
    { headers: { 'Content-Type': 'application/json' } });

  check(r, { 'add 200': v => v.status === 200, 'ok==true': v => v.json('ok') === true });
}
