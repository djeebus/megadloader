const API_ROOT = process.env.API_ROOT || ''

export function addMegaLink (megaUrl, category) {
  return dispatch => {
    const body = new URLSearchParams()

    body.append('mega_url', megaUrl)
    if (category) {
      body.append('category', category)
    }

    fetch(`${API_ROOT}/api/urls/`, {
      body: body,
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(results => {
      return results.json()
    }).then(data => {
      dispatch(urlAddSucceeded(megaUrl, category, data))
    }, err => {
      dispatch(urlAddFailed(megaUrl, category, err))
    })
  }
}

export const URL_ADD_SUCCEEDED = 'URL_ADD_SUCCEEDED'
function urlAddSucceeded (megaUrl, category) {
  return {
    type: URL_ADD_SUCCEEDED,
    megaUrl,
    category
  }
}

export const URL_ADD_FAILED = 'URL_ADD_FAILED'
function urlAddFailed (megaUrl, category, error) {
  return {
    type: URL_ADD_FAILED,
    megaUrl,
    category,
    error
  }
}

export const QUEUE_REFRESHING = 'QUEUE_REFRESHING'
export const QUEUE_REFRESHED = 'QUEUE_REFRESHED'

export function refreshQueue () {
  return dispatch => {
    dispatch({ type: QUEUE_REFRESHING })

    fetch(`${API_ROOT}/api/status`)
      .then(res => res.json())
      .then(response => {
        dispatch({
          type: QUEUE_REFRESHED,
          data: response
        })
      })
  }
}

const QUEUE_ITEM_REMOVING = 'QUEUE_ITEM_REMOVING'
const QUEUE_ITEM_REMOVED = 'QUEUE_ITEM_REMOVED'

export function removeQueueItem (queueId) {
  return dispatch => {
    dispatch({ type: QUEUE_ITEM_REMOVING })

    fetch(`${API_ROOT}/api/queue/${queueId}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(response => {
        dispatch({
          type: QUEUE_ITEM_REMOVED,
          data: response
        })

        const queueRefresher = refreshQueue()
        queueRefresher(dispatch)
      })
  }
}

export const CATEGORIES_REFRESHING = 'CATEGORIES_REFRESHING'
export const CATEGORIES_REFRESHED = 'CATEGORIES_REFRESHED'

export function refreshCategories () {
  return dispatch => {
    dispatch({ type: CATEGORIES_REFRESHING })

    fetch(`${API_ROOT}/api/categories/`)
      .then(res => res.json())
      .then(response => {
        dispatch({
          type: CATEGORIES_REFRESHED,
          items: response
        })
      })
  }
}

export const ADDING_CATEGORY = 'ADDING_CATEGORY'
export const ADDED_CATEGORY = 'ADDED_CATEGORY'

export function addCategory (name) {
  return dispatch => {
    dispatch({ type: ADDING_CATEGORY })

    fetch(`${API_ROOT}/api/categories/`, {
      method: 'POST',
      body: JSON.stringify({ name })
    })
      .then(res => res.json())
      .then(response => {
        dispatch({
          type: ADDED_CATEGORY,
          category: response
        })
      })
  }
}
