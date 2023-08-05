import { post } from '../utils/request';

export const registerService = (params) => post('/api/accounts/signup', params);
