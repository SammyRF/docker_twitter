import { get } from '../utils/request';

export const loginService = (username, password) => get(`/api/login/${username}/${password}`);
