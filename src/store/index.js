import {createStore, combineReducers, applyMiddleware} from 'redux'
import thunkMiddleware from 'redux-thunk'

import queue from './queue'

const rootReducer = combineReducers({ queue })
const store = createStore(
    rootReducer,
    applyMiddleware(
        thunkMiddleware,
    ),
)
export default store
