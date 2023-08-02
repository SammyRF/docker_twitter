import { Button, Calendar, Input } from 'antd-mobile';

import { useState } from 'react';
import moment from 'moment';
import style from './index.module.css';
import Header from '../../components/Header';
import TInput from '../../components/TInput';

const Register = () => {
  const [date, setDate] = useState(new Date('2000-01-01'));
  const [canRigester, setCanRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [phone, setPhone] = useState('');

  const onUsernameChangedHandler = (v) => {
    setUsername(v);
    setCanRegister(v !== '' && phone !== '');
  };

  const onPhoneChangedHandler = (v) => {
    setPhone(v);
    setCanRegister(username !== '' && v !== '');
  };

  return (
    <div>
      <Header />
      <TInput label="Username" onChange={onUsernameChangedHandler} value={username} />
      <TInput label="Phone" onChange={onPhoneChangedHandler} value={phone} />
      <Input
        className={style.inputBox}
        placeholder="Birthday"
        disabled
        clearable
        value={moment(date).format('YYYY-MM-DD')}
      />
      <Calendar
        className={style.calendarBox}
        selectionMode="single"
        defaultValue={date}
        onChange={(d) => d !== null && setDate(d)}
      />
      <Button
        className={style.registerButton}
        color="primary"
        block
        size="Large"
        disabled={!canRigester}
        onClick={() => alert(`${username} : ${phone} : ${moment(date).format('YYYY-MM-DD')}`)}
      >
        Register
      </Button>
    </div>
  );
};

export default Register;
