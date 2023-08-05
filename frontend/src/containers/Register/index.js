import {
  Button, Calendar, Input, Toast,
} from 'antd-mobile';

import { useState } from 'react';
import moment from 'moment';
import style from './index.module.css';
import TInput from '../../components/TInput';
import { registerService } from '../../services/register';
import Show from '../../components/Show';
import { useGlobalContext } from '../../utils/context';

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

  const onRegisterButtonClick = async () => {
    try {
      const res = await registerService({
        id: username,
        username,
        phone,
        birthday: moment(date).format('YYYY-MM-DD'),
      });
      if (res.id === username) {
        Toast.show('register succeeded.');
      }
    } catch (_e) {
      Toast.show('register failed.');
    }
  };

  const [store] = useGlobalContext();

  return (
    <Show visible={store === 'register'}>
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
        onClick={onRegisterButtonClick}
      >
        Register
      </Button>
    </Show>
  );
};

export default Register;
