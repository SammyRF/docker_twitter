import { Button, Calendar, Input } from 'antd-mobile';

import { useState } from 'react';
import moment from 'moment';
import style from './index.module.css';
import Header from '../../components/Header';
import TInput from '../../components/TInput';

const Register = () => {
  const [date, setDate] = useState(new Date('2000-01-01'));

  return (
    <div>
      <Header />
      <TInput label="Username" />
      <TInput label="Phone" />
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
      >
        Register
      </Button>
    </div>
  );
};

export default Register;
