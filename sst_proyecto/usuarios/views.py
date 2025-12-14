from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from .models import Usuario, Visitante
from .serializers import UsuarioSerializer, LoginSerializer, VisitanteSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        # Permitir registro sin autenticación
        if self.action in ['login', 'create']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Registro de nuevos usuarios - Simplificado"""
        try:
            # Validar contraseñas coincidan
            password = request.data.get('password')
            password2 = request.data.get('password2')
            
            if not password or not password2:
                return Response(
                    {'error': 'Debes proporcionar ambas contraseñas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if password != password2:
                return Response(
                    {'error': 'Las contraseñas no coinciden'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(password) < 8:
                return Response(
                    {'error': 'La contraseña debe tener al menos 8 caracteres'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar campos requeridos
            username = request.data.get('username')
            email = request.data.get('email')
            numero_documento = request.data.get('numero_documento')
            tipo_documento = request.data.get('tipo_documento')
            rol = request.data.get('rol')
            
            if not all([username, email, numero_documento, tipo_documento, rol]):
                return Response(
                    {'error': 'Todos los campos son obligatorios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el documento no exista
            if Usuario.objects.filter(numero_documento=numero_documento).exists():
                return Response(
                    {'error': 'Ya existe un usuario con este número de documento'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el username no exista
            if Usuario.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Este nombre de usuario ya está en uso'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el email no exista
            if Usuario.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Este correo electrónico ya está registrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear usuario
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
            )
            
            # Crear token
            token, created = Token.objects.get_or_create(user=usuario)
            
            return Response({
                'id': usuario.id,
                'username': usuario.username,
                'email': usuario.email,
                'rol': usuario.rol,
                'token': token.key,
                'mensaje': 'Usuario registrado exitosamente. Ya puedes iniciar sesión.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear el usuario: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data['usuario']
        login(request, usuario)
        token, created = Token.objects.get_or_create(user=usuario)

        return Response({
            'token': token.key,
            'usuario': UsuarioSerializer(usuario).data,
            'mensaje': 'Login exitoso.'
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({'mensaje': 'Logout exitoso.'})
    
    @action(detail=False, methods=['get'])
    def perfil(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
class VisitanteViewSet(viewsets.ModelViewSet):
    queryset = Visitante.objects.all()
    serializer_class = VisitanteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)