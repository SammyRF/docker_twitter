import {
  createContext, useContext, useMemo, useState,
} from 'react';
import PropTypes from 'prop-types';

const GlobalContext = createContext();

export const GlobalContextProvider = ({ children }) => {
  const [store, setStore] = useState('login');

  const val = useMemo(() => ({ store, setStore }), [store]);

  return <GlobalContext.Provider value={val}>{children}</GlobalContext.Provider>;
};

GlobalContextProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  return [context.store, context.setStore];
};
