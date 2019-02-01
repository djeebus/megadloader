import {QUEUE_REFRESHING, QUEUE_REFRESHED} from '../actions'

const initialState = {
    isRefreshing: false,
    items: [],
}

function queue(state = initialState, action) {
    switch (action.type) {
        case QUEUE_REFRESHING:
            return {
                ...state,
                isRefreshing: true,
            }
        case QUEUE_REFRESHED:
            return {
                ...state,
                isRefreshing: false,
                items: action.data.urls,
            }

        default:
            return state
    }
}

export default queue