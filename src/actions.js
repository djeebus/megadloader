export function addMegaLink(megaUrl, category) {
    return dispatch => {
        const body = new URLSearchParams()

        body.append('mega_url', megaUrl)
        if (category) {
            body.append('category', category)
        }

        fetch('/api/urls/', {
            body: body,
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
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
function urlAddSucceeded(megaUrl, category) {
    return {
        type: URL_ADD_SUCCEEDED,
        megaUrl,
        category,
    }
}

export const URL_ADD_FAILED = 'URL_ADD_FAILED'
function urlAddFailed(megaUrl, category, error) {
    return {
        type: URL_ADD_FAILED,
        megaUrl,
        category,
        error,
    }
}

export const QUEUE_REFRESHING = 'QUEUE_REFRESHING'
export const QUEUE_REFRESHED = 'QUEUE_REFRESHED'

export function refreshQueue() {
    return dispatch => {
        dispatch({type: QUEUE_REFRESHING})

        fetch('/api/status')
            .then(res => res.json())
            .then(response => {
                dispatch({
                    type: QUEUE_REFRESHED,
                    data: response,
                })
            })
    }
}
