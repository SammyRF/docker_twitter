import axios from 'axios';

const domain = 'http://localhost:3333';

// hijack request
axios.interceptors.request.use((config) => ({
  ...config,
  url: domain + config.url,
}));

// hijack response
axios.interceptors.response.use((response) => {
  console.log(response.data);
  return response.data;
}, (err) => Promise.reject(err));

export const get = (url) => axios.get(url);
export const post = (url, params) => axios.post(url, params);
export const put = (url, params) => axios.put(url, params);
export const patch = (url, params) => axios.patch(url, params);
export const del = (url, params) => axios.delete(url, params);
