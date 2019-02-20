import {createStore, combineReducers, applyMiddleware} from 'redux'
import thunkMiddleware from 'redux-thunk'

import categories from './categories'
import queue from './queue'

const rootReducer = combineReducers({ categories, queue })
const store = createStore(
    rootReducer,
    applyMiddleware(
        thunkMiddleware,
    ),
)
export default store
