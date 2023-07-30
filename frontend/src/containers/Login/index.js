import { Button, Form, Input } from 'antd-mobile';
import './index.css';
import { useState } from 'react';

const Login = () => {
  const [form] = Form.useForm();
  const onSubmit = () => {
    const vals = form.getFieldsValue();
    // eslint-disable-next-line no-alert, no-undef
    alert(`${vals.username} : ${vals.password}`);
  };

  const [canLogin, setCanLogin] = useState(false);
  const textChangeHandler = () => {
    const vals = form.getFieldsValue();
    const hasUsername = vals.username !== null && vals.username !== '' && typeof vals.username !== 'undefined';
    const hasPassword = vals.password !== null && vals.password !== '' && typeof vals.password !== 'undefined';
    setCanLogin(hasUsername && hasPassword);
  };

  return (
    <div className="Login">
      <Form
        name="Login"
        class-name="login-form"
        form={form}
        layout="horizontal"
        mode="card"
        footer={(<Button color="primary" block size="Large" onClick={onSubmit} disabled={!canLogin}>Login</Button>)}
      >
        <Form.Item name="username" rules={[{ required: true, message: 'Please input your Username!' }]}>
          <Input placeholder="Username" clearable onChange={textChangeHandler} />
        </Form.Item>
        <Form.Item name="password" rules={[{ required: true, message: 'Please input your Password!' }]}>
          <Input type="password" placeholder="Password" clearable onChange={textChangeHandler} />
        </Form.Item>
      </Form>
    </div>
  );
};

export default Login;
