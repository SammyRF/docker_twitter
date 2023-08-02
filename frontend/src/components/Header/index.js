import { CloseOutline } from 'antd-mobile-icons';
import logo from '../../assets/header_logo.svg';

import style from './index.module.css';

const Header = () => (
  <div className={style.headerDiv}>
    <CloseOutline className={style.closeIcon} />
    <img className={style.logo} src={logo} alt="logo" />
  </div>
);

export default Header;
