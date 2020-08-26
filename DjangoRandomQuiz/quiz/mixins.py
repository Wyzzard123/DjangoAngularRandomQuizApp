from rest_framework.exceptions import PermissionDenied


class NoUpdateCreatorMixin:
    """Do not allow users to change the creator of the resource."""
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Do not allow anyone to change the creator
        if int(request.data['creator']) != instance.creator.id:
            raise PermissionDenied("You do not have permission to update this resource.")

        return super().update(request, *args, **kwargs)
