import { useState } from 'react';
import './index.css';

const Login = () => {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')

    const onClickHandler = () => {
        alert(username + ' : ' + password)
    }

    const onUsernameChangeHandler = (e) => {
        setUsername(e.target.value)
    }

    const onPasswordChangeHandler = (e) => {
        setPassword(e.target.value)
    }
    
    return (
        <div className="Login">
            <div>
                <input value={username} placeholder='Username' clearable onChange={onUsernameChangeHandler}/>
            </div>
            <div>
                <input value={password} type='password' placeholder='Password' clearable onChange={onPasswordChangeHandler}/>
            </div>
            <div>
                <button onClick={onClickHandler}>login</button>
            </div>
        </div>
    );
}

export default Login;
