import { CloseOutline } from 'antd-mobile-icons';
import logo from '../../assets/header_logo.svg';

import style from './index.module.css';
import { useGlobalContext } from '../../utils/context';

const Header = () => {
  const [store, setStore] = useGlobalContext();

  return (
    <div className={style.headerDiv}>
      <CloseOutline className={style.closeIcon} onClick={() => setStore(store === 'login' ? 'register' : 'login')} />
      <img className={style.logo} src={logo} alt="logo" />
    </div>
  );
};

export default Header;
