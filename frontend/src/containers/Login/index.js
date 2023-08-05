import { Button, Toast } from 'antd-mobile';
import { useState } from 'react';
import style from './index.module.css';
import { loginService } from '../../services/login';
import TInput from '../../components/TInput';
import Show from '../../components/Show';
import { useGlobalContext } from '../../utils/context';

const Login = () => {
  const [username, setUsername] = useState('');
  const [canLogin, setCanLogin] = useState(false);

  const onLogin = async () => {
    const res = await loginService(username);
    Toast.show(res && res.length > 0 ? 'login succeeded' : 'login failed');
  };

  const onTextChangeHandler = (v) => {
    setUsername(v);
    setCanLogin(v !== '');
  };

  const [store] = useGlobalContext();

  return (
    <Show visible={store === 'login'}>
      <div className={style.tinputBox}>
        <TInput label="username" onChange={onTextChangeHandler} value={username} />
      </div>
      <Button className={style.loginButton} color="primary" block size="Large" onClick={onLogin} disabled={!canLogin}>Login</Button>
    </Show>
  );
};

export default Login;
