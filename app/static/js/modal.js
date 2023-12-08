const ModalResponseToComment = document.getElementById('modal_response_to_comment')
if (ModalResponseToComment) {
  ModalResponseToComment.addEventListener('show.bs.modal', event => {
  const button = event.relatedTarget

  const recipient = button.getAttribute('data-bs-whatever')
  const modalTitle = ModalResponseToComment.querySelector('.modal-title')

  const group_id = button.getAttribute('data-bs-group-id')
  const modalGroup = ModalResponseToComment.querySelector('.response-to-comment-group-id')

  const post_id = button.getAttribute('data-bs-post-id')
  const modalPost = ModalResponseToComment.querySelector('.response-to-comment-post-id')
  
  const comment_id = button.getAttribute('data-bs-comment-id')
  const modalComment = ModalResponseToComment.querySelector('.response-to-comment-comment-id')

  modalTitle.textContent = `Ответить на комментарий «${recipient}»`
  modalGroup.value = `${group_id}`
  modalPost.value = `${post_id}`
  modalComment.value = `${comment_id}`
  })
}