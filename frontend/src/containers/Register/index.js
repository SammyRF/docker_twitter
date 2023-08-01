import { Button, Calendar, Input } from 'antd-mobile';

import { useState } from 'react';
import style from './index.module.css';
import Header from '../../components/Header';

const Register = () => {
  const [date, setDate] = useState(new Date('2000-01-01'));
  const onDateChangeHandler = (d) => {
    setDate(d);
  };

  return (
    <div>
      <Header />
      <Input className={style.inputBox} placeholder="Username" clearable />
      <Input className={style.inputBox} placeholder="Phone" clearable />
      <Input className={style.inputBox} placeholder="Birthday" disabled clearable value={date.toLocaleDateString()} />
      <Calendar className={style.calendarBox} selectionMode="single" defaultValue={date} onChange={onDateChangeHandler} />
      <Button className={style.registerButton} color="primary" block size="Large">Register</Button>
    </div>
  );
};

export default Register;
