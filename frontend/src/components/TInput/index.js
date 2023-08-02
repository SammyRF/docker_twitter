import { useState } from 'react';
import { Input } from 'antd-mobile';
import { PropTypes } from 'prop-types';

import style from './index.module.css';

const TInput = ({
  label, maxLen, onChange,
}) => {
  const [isFocused, setFocused] = useState(false);
  const [value, setValue] = useState('');
  const onChangeHandler = (val) => {
    // eslint-disable-next-line no-unused-expressions
    val.length <= maxLen && setValue(val);
    onChange(val);
  };

  return (
    <div className={isFocused ? style.tInputFocused : style.tInput}>
      <div className={isFocused || value.length > 0 ? style.tLableFocused : style.tLabel}>
        {label}
        <span className={style.labelRight}>
          {value.length}
          /
          {maxLen}
        </span>
      </div>
      <Input
        className={isFocused || value.length > 0 ? style.inputItemFocused : style.inputItem}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        value={value}
        onChange={onChangeHandler}
      />
    </div>
  );
};

TInput.propTypes = {
  label: PropTypes.string,
  maxLen: PropTypes.number,
  onChange: PropTypes.func,
};

TInput.defaultProps = {
  label: '',
  maxLen: 10,
  onChange: () => {},
};

export default TInput;
