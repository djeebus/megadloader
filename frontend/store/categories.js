import { CATEGORIES_REFRESHING, CATEGORIES_REFRESHED, ADDED_CATEGORY } from '../actions'

const initialState = {
  isRefreshing: false,
  items: []
}

export default function (state = initialState, action) {
  switch (action.type) {
    case CATEGORIES_REFRESHING:
      return {
        ...state,
        isRefreshing: true
      }

    case CATEGORIES_REFRESHED:
      return {
        ...state,
        isRefreshing: false,
        items: action.items
      }

    case ADDED_CATEGORY:
      return {
        ...state,
        items: [
          ...state.items,
          action.category
        ]
      }

    default:
      return state
  }
}
